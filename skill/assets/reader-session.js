/* Shared portable bookmark contract. No DOM, storage, network, or execution of source text. */
(function (root) {
  "use strict";
  const MAX_BYTES = 1024 * 1024;
  const fail = (message) => { throw new Error("书签无效：" + message); };
  const object = (value, keys, label) => {
    if (!value || typeof value !== "object" || Array.isArray(value) ||
        Object.keys(value).sort().join(",") !== keys.slice().sort().join(",")) fail(label + "字段不匹配。");
  };
  const validString = (value, max) => {
    if (typeof value !== "string" || Array.from(value).length > max) return false;
    for (let i = 0; i < value.length; i++) {
      const code = value.charCodeAt(i);
      if (code >= 0xD800 && code <= 0xDBFF) {
        const next = value.charCodeAt(++i);
        if (!(next >= 0xDC00 && next <= 0xDFFF)) return false;
      } else if (code >= 0xDC00 && code <= 0xDFFF) return false;
    }
    return true;
  };
  const boundary = (text, offset) => Number.isSafeInteger(offset) && offset >= 0 && offset <= text.length &&
    !(offset > 0 && offset < text.length && text.charCodeAt(offset) >= 0xDC00 && text.charCodeAt(offset) <= 0xDFFF &&
      text.charCodeAt(offset - 1) >= 0xD800 && text.charCodeAt(offset - 1) <= 0xDBFF);
  const position = (text, offset) => {
    if (!boundary(text, offset)) fail("位置越界或切断了字符。");
    // At most 128 UTF-16 units contain the first 64 Unicode code points.
    const tail = text.slice(offset, offset + 128);
    return { offset, anchor: Array.from(tail).slice(0, 64).join("") };
  };
  const create = (data) => ({
    schema: "adhd-md-session", version: 1,
    source: { name: data.source_name, hash: data.source_hash, length: data.source_text.length },
    current: position(data.source_text, 0), resume: position(data.source_text, 0),
    presented: [], skipped: [], questions: [], paused: false, ended: false,
  });
  const normalizeRanges = (ranges, text) => {
    if (!Array.isArray(ranges) || ranges.length > 10000) fail("范围数量不合法。");
    const sorted = ranges.map((range) => {
      if (!Array.isArray(range) || range.length !== 2 || !boundary(text, range[0]) ||
          !boundary(text, range[1]) || range[0] >= range[1]) fail("范围越界或切断了字符。");
      return range.slice();
    }).sort((a, b) => a[0] - b[0]);
    const result = [];
    for (const range of sorted) {
      const previous = result[result.length - 1];
      if (previous && range[0] < previous[1]) fail("范围互相重叠。");
      if (previous && range[0] === previous[1]) previous[1] = range[1];
      else result.push(range);
    }
    return result;
  };
  const validate = (value, data) => {
    object(value, ["schema", "version", "source", "current", "resume", "presented", "skipped", "questions", "paused", "ended"], "会话");
    if (value.schema !== "adhd-md-session" || value.version !== 1) fail("不支持此会话版本。");
    object(value.source, ["name", "hash", "length"], "来源");
    if (!validString(value.source.name, 4096) || typeof value.source.hash !== "string" ||
        !/^[0-9a-f]{64}$/.test(value.source.hash) || !Number.isSafeInteger(value.source.length) || value.source.length < 0) fail("来源格式不合法。");
    if (value.source.hash !== data.source_hash || value.source.length !== data.source_text.length) {
      fail("原文版本不匹配。请保留书签，按原文锚点核对位置后重新建立会话。");
    }
    const checkPosition = (value) => {
      object(value, ["offset", "anchor"], "位置");
      const expected = position(data.source_text, value.offset);
      if (!validString(value.anchor, 64) || value.anchor !== expected.anchor) fail("原文锚点不匹配。");
      return expected;
    };
    const current = checkPosition(value.current), resume = checkPosition(value.resume);
    const presented = normalizeRanges(value.presented, data.source_text);
    const skipped = normalizeRanges(value.skipped, data.source_text);
    let i = 0, j = 0;
    while (i < presented.length && j < skipped.length) {
      if (presented[i][0] < skipped[j][1] && skipped[j][0] < presented[i][1]) fail("已展示与跳过范围重叠。");
      if (presented[i][1] <= skipped[j][0]) i++; else j++;
    }
    if (!Array.isArray(value.questions) || value.questions.length > 100 ||
        value.questions.some((q) => !validString(q, 1000) || /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]*$/.test(q))) fail("疑问须为非空文字，每条最多1000字、共100条。");
    if (typeof value.paused !== "boolean" || typeof value.ended !== "boolean") fail("暂停或结束状态格式不合法。");
    return { schema: "adhd-md-session", version: 1,
      source: { name: data.source_name, hash: data.source_hash, length: data.source_text.length },
      current, resume, presented, skipped, questions: value.questions.slice(), paused: value.paused, ended: value.ended };
  };
  const parse = (text, data) => {
    if (new TextEncoder().encode(text).length > MAX_BYTES) fail("文件超过 1 MiB。");
    let value;
    try { value = JSON.parse(text); } catch (_) { fail("请粘贴完整的 JSON 书签。"); }
    // JSON.parse accepts duplicate keys. Reject them to match the CLI and avoid
    // silently changing what a bookmark author thought they had exported.
    const tokens = /"(?:\\["\\/bfnrt]|\\u[0-9a-fA-F]{4}|[^"\\\x00-\x1f])*"|[{}\[\],:]|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/g;
    const stack = [];
    let token, previous;
    while ((token = tokens.exec(text))) {
      const current = token[0];
      if (/^-?\d/.test(current) && !/^-?(?:0|[1-9]\d*)$/.test(current)) fail("位置、范围和版本必须使用整数。");
      if (current === "{") stack.push(new Set());
      else if (current === "[") stack.push(null);
      else if (current === "}" || current === "]") stack.pop();
      else if (current === ":") {
        const key = JSON.parse(previous), keys = stack[stack.length - 1];
        if (keys.has(key)) fail("JSON 含重复字段。");
        keys.add(key);
      }
      previous = current;
    }
    return validate(value, data);
  };
  const add = (ranges, start, end) => {
    if (start >= end) return ranges.map((r) => r.slice());
    const sorted = ranges.concat([[start, end]]).sort((a, b) => a[0] - b[0]);
    const result = [];
    for (const range of sorted) {
      const previous = result[result.length - 1];
      if (previous && range[0] <= previous[1]) previous[1] = Math.max(previous[1], range[1]);
      else result.push(range.slice());
    }
    return result;
  };
  const remove = (ranges, start, end) => ranges.flatMap(([a, b]) => {
    if (end <= a || start >= b) return [[a, b]];
    return (a < start ? [[a, start]] : []).concat(b > end ? [[end, b]] : []);
  });
  const overlap = (ranges, start, end) => ranges.some(([a, b]) => a < end && start < b);
  const api = { MAX_BYTES, position, create, validate, parse, add, remove, overlap };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.AdhdReadingSession = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
