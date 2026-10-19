/* State-only harness: execute the generated reader scripts without a browser.
 * This intentionally does not model layout, accessibility, or browser rendering.
 */
"use strict";
const fs = require("fs");
const vm = require("vm");

async function run(request) {
  const storage = new Map(Object.entries(request.storage || {}));
  const downloads = [];
  let page, pageHtml = request.html, pathname = request.pathname || "/reading.reader.html";

  function launch() {
    const nodes = [], ids = new Map(), views = [];
    const urls = new Map();
    let clipboard = "", urlNumber = 0;

    class Element {
      constructor(tagName = "div") {
        this.tagName = tagName.toUpperCase();
        this.children = []; this.parentElement = null; this.listeners = new Map();
        this.attributes = {}; this.dataset = {}; this.style = { setProperty() {} };
        this.hidden = false; this.disabled = false; this.open = false;
        this.className = ""; this.textContent = ""; this.value = ""; this.checked = false;
        this.classList = { toggle: (name, enabled) => {
          const classes = new Set(this.className.split(/\s+/).filter(Boolean));
          if (enabled) classes.add(name); else classes.delete(name);
          this.className = Array.from(classes).join(" ");
        } };
        nodes.push(this);
      }
      setAttribute(name, value) { this.attributes[name] = String(value); }
      removeAttribute(name) { delete this.attributes[name]; }
      append(...children) {
        for (const child of children) { child.parentElement = this; this.children.push(child); }
      }
      replaceChildren(...children) {
        for (const child of this.children) child.parentElement = null;
        this.children = []; this.append(...children);
      }
      get childElementCount() { return this.children.length; }
      get firstElementChild() {
        // Only the tag name is consumed by the real UI's heading-style toggle.
        const match = /^\s*<([a-z][a-z0-9]*)\b/i.exec(this.innerHTML || "");
        return match ? { tagName: match[1].toUpperCase() } : this.children[0] || null;
      }
      addEventListener(name, handler) {
        if (!this.listeners.has(name)) this.listeners.set(name, []);
        this.listeners.get(name).push(handler);
      }
      async dispatch(name, properties = {}) {
        const event = { target: this, defaultPrevented: false,
          preventDefault() { this.defaultPrevented = true; }, ...properties };
        for (const handler of this.listeners.get(name) || []) await handler(event);
      }
      async click() {
        if (this.disabled) return;
        if (this.tagName === "A" && this.download && urls.has(this.href)) {
          downloads.push({ name: this.download, blob: urls.get(this.href) });
        }
        await this.dispatch("click");
      }
      remove() {
        if (this.parentElement) {
          this.parentElement.children = this.parentElement.children.filter(child => child !== this);
          this.parentElement = null;
        }
      }
      focus() {} select() {} scrollIntoView() {}
      closest() { return null; }
    }

    // Read static IDs and view buttons from the generated markup. Do not create
    // missing IDs on demand: removing a real control must make this harness fail.
    const markup = pageHtml.slice(0, pageHtml.indexOf("<script"));
    for (const tag of markup.matchAll(/<([a-z][a-z0-9]*)\b([^>]*)>/gi)) {
      const attributes = {};
      for (const attribute of tag[2].matchAll(/([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) {
        attributes[attribute[1]] = attribute[2] ?? attribute[3] ?? attribute[4] ?? "";
      }
      if (!("id" in attributes) && !("data-view" in attributes)) continue;
      const node = new Element(tag[1]);
      node.attributes = attributes;
      node.hidden = "hidden" in attributes; node.open = "open" in attributes;
      node.className = attributes.class || "";
      if (attributes.id) { node.id = attributes.id; ids.set(node.id, node); }
      if (attributes["data-view"]) { node.dataset.view = attributes["data-view"]; views.push(node); }
    }
    const scripts = Array.from(pageHtml.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi));
    const dataScript = scripts.find(script => /\bid=["']reader-data["']/.test(script[1]));
    if (!dataScript) throw new Error("generated HTML has no reader-data script");
    const dataNode = new Element("script");
    dataNode.textContent = dataScript[2]; ids.set("reader-data", dataNode);
    const executable = scripts.filter(script => !/\btype=["']application\/json["']/.test(script[1]));
    if (executable.length !== 2) throw new Error("expected the real protocol and reader UI scripts");
    const required = id => {
      const element = ids.get(id);
      if (!element) throw new Error("missing reader control: " + id);
      return element;
    };
    const document = {
      body: new Element("body"), documentElement: new Element("html"), title: "",
      getElementById: id => ids.get(id) || null,
      createElement: name => new Element(name),
      createTextNode: text => ({ textContent: text, parentElement: null }),
      addEventListener() {},
      querySelectorAll(selector) {
        if (selector === "[data-view]") return views;
        if (selector === ".toc-button") return nodes.filter(node => node.className.split(/\s+/).includes("toc-button"));
        throw new Error("unsupported selector in state harness: " + selector);
      },
      querySelector(selector) {
        const view = /^\[data-view="([^"]+)"\]$/.exec(selector);
        if (view) return views.find(node => node.dataset.view === view[1]) || null;
        throw new Error("unsupported selector in state harness: " + selector);
      },
    };
    class BrowserURL extends URL {
      static createObjectURL(blob) {
        const url = "blob:state-test/" + (++urlNumber);
        urls.set(url, blob); return url;
      }
      static revokeObjectURL(url) { urls.delete(url); }
    }
    const context = vm.createContext({
      document, Blob, URL: BrowserURL, TextEncoder, TextDecoder,
      location: { pathname, protocol: "file:" },
      navigator: { clipboard: { async writeText(text) { clipboard = text; } } },
      localStorage: {
        getItem(key) {
          if (request.failStorage) throw new Error("storage unavailable");
          return storage.get(key) ?? null;
        },
        setItem(key, value) {
          if (request.failStorage) throw new Error("storage unavailable");
          storage.set(key, String(value));
        },
      },
      matchMedia: () => ({ matches: false }), addEventListener() {},
      // Object URLs remain alive for the test; no actual timer or I/O is needed.
      setTimeout() { return 0; },
    });
    context.window = context;
    executable.forEach((script, index) => vm.runInContext(script[2], context,
      { filename: "generated-reader-script-" + index + ".js", timeout: 5000 }));
    if (!required("fatal-panel").hidden) throw new Error(required("fatal-panel").textContent);
    return { required, document, clipboard: () => clipboard };
  }

  async function snapshot() {
    const read = page.required;
    const result = {
      location: read("location-label").textContent,
      pauseHidden: read("pause-view").hidden, resumeHidden: read("resume-bar").hidden,
      fullHidden: read("full-view").hidden, message: read("session-message").textContent,
      messageError: read("session-message").dataset.error,
      storageNote: read("storage-note").textContent,
    };
    // Observe the public export control, never reach into lexical state or
    // reconstruct session updates in this harness.
    await read("copy-session").click();
    result.session = JSON.parse(page.clipboard());
    result.storage = Object.fromEntries(storage);
    result.downloads = await Promise.all(downloads.map(async item => ({
      name: item.name, text: await item.blob.text(),
    })));
    return result;
  }

  page = launch();
  const snapshots = [];
  for (const operation of request.operations || []) {
    if (operation.type === "click") await page.required(operation.id).click();
    else if (operation.type === "toc") {
      const buttons = page.document.querySelectorAll(".toc-button");
      if (!buttons[operation.index]) throw new Error("missing TOC entry");
      await buttons[operation.index].click();
    } else if (operation.type === "view") {
      const button = page.document.querySelector('[data-view="' + operation.view + '"]');
      if (!button) throw new Error("missing view button");
      await button.click();
    } else if (operation.type === "fill") page.required(operation.id).value = operation.value;
    else if (operation.type === "file") {
      const input = page.required("session-file"), bytes = Uint8Array.from(operation.bytes);
      input.files = [{ size: bytes.length, async arrayBuffer() { return bytes.buffer; } }];
      await input.dispatch("change");
    } else if (operation.type === "navigate") {
      pageHtml = operation.html; pathname = operation.pathname; page = launch();
    }
    else if (operation.type === "reload") page = launch();
    else if (operation.type === "snapshot") snapshots.push(await snapshot());
    else throw new Error("unsupported operation: " + operation.type);
  }
  return snapshots;
}

run(JSON.parse(fs.readFileSync(0, "utf8"))).then(result => {
  process.stdout.write(JSON.stringify(result));
}).catch(error => { process.stderr.write(error.stack + "\n"); process.exitCode = 1; });
