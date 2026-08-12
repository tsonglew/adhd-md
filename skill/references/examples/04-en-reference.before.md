# renderMarkdown

### renderMarkdown(input, options)

Renders a Markdown string to HTML. **Returns** a **Promise** that **resolves** to an **object** with **html** and **meta** keys.

**Parameters**
- input — string — the Markdown source. Required.
- options.gfm — boolean — enable GitHub Flavored Markdown. Default true.
- options.sanitize — boolean — strip raw HTML from the output. Default true. Setting this to false allows arbitrary HTML through, which is a security risk if the input is user-supplied, so only disable it for trusted content such as your own documentation files.
- options.highlight — function — called with (code, lang) for each fenced block. Should return an HTML string. If it throws, the block is rendered unhighlighted and the error is swallowed.

**Example**
```
const { html } = await renderMarkdown('# hi', { gfm: false })
```

**Throws** TypeError if input is not a string.
