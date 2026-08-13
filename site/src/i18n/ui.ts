/**
 * 站点文案。中文是主语言，英文是翻译。
 * 带 _html 后缀的字段允许内联 <code> 等标记（内容来自本文件，不经用户输入）。
 */
const zh = {
  lang: "zh-CN",
  otherUrl: "/adhd-md/en/",
  meta: {
    title: "adhd-md — 把 Markdown 改造成读得下去的样子",
    description:
      "一份跨 agent 通用的 skill：把 Markdown 改造成 ADHD 友好、可扫读的版本。可只改格式、只改内容或两者兼改。只重排信息，绝不删信息。格式档的改动可被脚本证明无损。",
    canonical: "https://tsonglew.github.io/adhd-md/",
    ogTitle: "adhd-md — 把 Markdown 改造成读得下去的样子",
    ogDescription:
      "一份 skill 通用于 Claude Code、Codex、Grok Build、Gemini CLI、Cursor、opencode。可只改格式、只改内容或两者兼改。只重排信息，绝不删信息。",
    ogImage: "https://tsonglew.github.io/adhd-md/og.png",
    ogImageAlt: "adhd-md：把 Markdown 改造成读得下去的样子。只重排信息，绝不删信息。脚本分 87.8 到 100，正文一个词都没改。",
    twitterTitle: "adhd-md — 把 Markdown 改造成读得下去的样子",
    twitterDescription: "一份 skill 通用于六个 agent。只重排信息，绝不删信息。格式档的改动可被脚本证明无损。",
    twitterImageAlt: "adhd-md 预览图：脚本分 87.8 到 100，正文一个词都没改。",
  },
  skip: "跳到正文",
  nav: ["对照", "三种改法", "去 AI 味", "无损", "宿主"],
  langSwitch: { label: "EN", href: "/adhd-md/en/" },
  themeToggle: { ariaToDark: "切换到暗色", ariaToLight: "切换到亮色" },
  footer: {
    tagline: "MIT · 纯标准库 Python，零依赖",
    links: [
      { label: "源码", href: "https://github.com/tsonglew/adhd-md" },
      { label: "规则库", href: "https://github.com/tsonglew/adhd-md/blob/main/skill/references/rules.md" },
      { label: "反模式", href: "https://github.com/tsonglew/adhd-md/blob/main/skill/references/antipatterns.md" },
      { label: "宿主矩阵", href: "https://github.com/tsonglew/adhd-md/blob/main/docs/host-matrix.md" },
      { label: "验证结论", href: "https://github.com/tsonglew/adhd-md/blob/main/docs/eval.md" },
      { label: "反馈问题", href: "https://github.com/tsonglew/adhd-md/issues/new/choose" },
    ],
  },
  hero: {
    eyebrow: "Agent Skill · 六个宿主通用",
    h1a: "把 Markdown 改造成",
    h1b: "读得下去",
    h1c: "的样子",
    lede: "结论前置、段落切碎、动作明确。在 Claude Code、Codex、Grok Build、Gemini CLI、Cursor、opencode 里都能用同一份 skill。",
    creed1: "只重排信息，绝不删信息。",
    creed2: "篇幅太长就折叠或移到附录。格式档的改动可被脚本证明无损。",
    buttons: ["看源码", "看对照"],
  },
  problem: {
    h2: "读不下去的文档，问题多半在排版",
    sub: "同一段信息，一坨读不下去，切开就能读。",
    wall:
      "md-cache 是一个 Markdown 渲染缓存中间件，把渲染结果按内容哈希缓存到本地磁盘，命中时直接返回，避免重复渲染。它需要 Node 18 以上版本，依赖只有一个 lru-cache。装好之后在渲染管线里包一层 withCache 就行。缓存目录默认是 .cache/md，可以用 MD_CACHE_DIR 环境变量改。默认最大条目数是 500，用 maxEntries 选项改。默认 TTL 是 7 天，用 ttl 选项改，单位是毫秒。设成 0 表示永不过期，但磁盘会一直涨，生产环境不建议。",
    proof: ["七件事挤在一段里", "结论还埋在最后"],
    cost: [
      { k: "回跳", t: "「如上所述」要求把眼睛移回去、重新定位、再回来。工作记忆一次强制清空重载" },
      { k: "埋结论", t: "读者在前 15 行决定去留。结论在第 40 行等于没写" },
      { k: "找不到下一步", t: "知道原理但不知道该敲什么，启动摩擦直接变成放弃" },
      { k: "AI 味", t: "「不是 A 而是 B」要读者先装载一个自己本来没有的误解，再卸掉" },
    ],
  },
  compare: {
    h2: "同一篇文档，一个词都没改",
    subHtml:
      "下面是真实语料。<code>scope=format</code> 档只动标记、空白和块顺序，正文词序列逐字保留。左右对照看看差别。",
    beforeTag: "改前",
    afterTag: "改后",
    scoreBefore: "87.8",
    scoreAfter: "100",
    docTitle: "md-cache",
    beforeParas: [
      "md-cache 是一个 Markdown 渲染缓存中间件，把渲染结果按内容哈希缓存到本地磁盘，命中时直接返回，避免重复渲染。它需要 Node 18 以上版本，依赖只有一个 lru-cache。装好之后在渲染管线里包一层 withCache 就行。缓存目录默认是 .cache/md，可以用 MD_CACHE_DIR 环境变量改。默认最大条目数是 500，用 maxEntries 选项改。默认 TTL 是 7 天，用 ttl 选项改，单位是毫秒。设成 0 表示永不过期，但磁盘会一直涨，生产环境不建议。",
      "如果渲染函数有副作用，不要用这个中间件，因为命中缓存时渲染函数根本不会被调用。如果你的 Markdown 里嵌了时间戳或随机数，输出会被缓存住，看起来像是不刷新，这不是 bug。",
      "实测在 1200 篇文档的站点上，冷启动构建 42 秒，二次构建 3.1 秒，快十三倍。",
    ],
    after: {
      moved: "实测在 1200 篇文档的站点上，冷启动构建 42 秒，二次构建 3.1 秒，快十三倍。",
      p1: "md-cache 是一个 Markdown 渲染缓存中间件，把渲染结果按内容哈希缓存到本地磁盘，命中时直接返回，避免重复渲染。",
      p2Html:
        "它需要 Node 18 以上版本，依赖只有一个 <code>lru-cache</code>。装好之后在渲染管线里包一层 <code>withCache</code> 就行。",
      list: [
        "缓存目录默认是 <code>.cache/md</code>，可以用 <code>MD_CACHE_DIR</code> 环境变量改。",
        "默认最大条目数是 500，用 <code>maxEntries</code> 选项改。",
        "默认 TTL 是 7 天，用 <code>ttl</code> 选项改，单位是毫秒。",
        "设成 0 表示永不过期，但磁盘会一直涨，生产环境不建议。",
      ],
      p3: "如果渲染函数有副作用，不要用这个中间件，因为命中缓存时渲染函数根本不会被调用。",
      p4: "如果你的 Markdown 里嵌了时间戳或随机数，输出会被缓存住，看起来像是不刷新，这不是 bug。",
    },
    dims: [
      { before: 40, after: 100, label: "首屏结论力" },
      { before: 92, after: 100, label: "分块粒度" },
      { before: 100, after: 100, label: "扫读性" },
      { before: 100, after: 100, label: "句子负荷" },
      { before: 100, after: 100, label: "行动性" },
      { before: 100, after: 100, label: "排版一致性" },
      { before: 100, after: 100, label: "活人感" },
    ],
    footChanged: "改动：结论块前置、一坨拆四段、四句配置转列表、裸标识符包成行内代码。",
    footWords: "新增词 0，删除词 0。",
    asideHtml:
      "注意改后没有给配置列表加小标题。「配置」这两个字原文里没有，加了就是新写措辞，越界成 <code>content</code>。结构可以大改，一个词都动不了，格式档的天花板就在这里。",
  },
  scope: {
    h2: "只改格式，只改内容，或者两者都改",
    sub: "划线判据只有一句话。搬移已有块算格式，写出新句子算内容。",
    cards: [
      {
        name: "format",
        lede: "正文词序列逐字不变，只动标记、空白、块顺序。",
        can: "能做",
        canText: "在已有句界拆段 · 并列句转列表（复用原词）· 加粗已有术语 · 块顺序重排 · 补代码块语言标签 · 折叠 · 中英文间距与标点规范",
        cant: "不能做",
        cantText: "改任何一个词 · 新写 TL;DR · 改写标题措辞",
        seal: "可证明无损",
      },
      {
        name: "content",
        lede: "只改措辞与信息组织，不碰排版风格。",
        can: "能做",
        canText: "长句拆短 · 被动改主动 · 新写 TL;DR · 标题改成结论式 · 补时间预估与下一步 · 术语首现解释 · 删填充词",
        cant: "不能做",
        cantText: "动排版结构 · 借「精简」之名删约束、单位、版本号、例外",
        seal: "不变量保全",
      },
      {
        name: "both",
        tag: "默认",
        lede: "先改内容再改格式，最后统一校验。",
        can: "另一根轴",
        canTextHtml:
          "<code>light</code> 只做零风险项，适合规范与 API 文档。<code>standard</code> 拆段、列表化、改标题、写 TL;DR。<code>deep</code> 全量重构骨架，适合会议记录和乱笔记。",
        cant: "怎么用",
        cantText: "直接说人话：「把 README 改成 ADHD 友好的，只改格式」",
        seal: "75 条规则按轴与档过滤",
      },
    ],
  },
  human: {
    h2: "顺手把 AI 味洗掉",
    sub: "模型写出来的中文有一些固定套路。每一种都要读者多花一次注意力，所以归这个 skill 管。",
    taxHead: ["套路", "读者多花的注意力"],
    tax: [
      { a: "不是 A 而是 B", b: "先装载一个自己本来没有的误解，再卸掉。白付一次工作记忆" },
      { a: "核心是：", b: "先宣布重要性再给货，等于把一句话说两遍" },
      { a: "值得注意的是", b: "承诺了深度，后面内容没变深，骗走一次注意力" },
      { a: "完成了对流程的优化", b: "动作藏进名词，要多解一层才知道谁做了什么" },
      { a: "赋能、闭环、全链路", b: "换成普通说法信息量不变，但读者要先翻译" },
      { a: "时间会保管细节", b: "没有主语能负责，读者无法核对真假" },
      { a: "大量测试、各种场景", b: "没有数字的量词，等于没给信息" },
      { a: "显著提升、彻底解决", b: "不写快了多少，读者无法核对" },
    ],
    grid1: {
      h: "破折号不硬禁，看密度",
      html: "<code>——</code> 是标准中文标点，用来插一句补充说明很正常。AI 味在于把它当节奏拐杖。实测手写技术文档中位数约 5 个/千字，模型生成常在 15 以上，所以阈值定在 8。列表里 <code>事项 —— 负责人 —— 期限</code> 是字段分隔，不计入。",
    },
    grid2: {
      h: "正则分不清的交给模型",
      html: "三个 flag 并列是好写法，「为什么出发，为什么放弃，为什么害怕」才要改，两者在正则眼里长得一样。所以同构排比与借喻只提示、不扣分。<code>git 仓库</code> 是本义，「记忆的仓库」才是包装。",
    },
  },
  lossless: {
    h2: "删一个词就会被拦下来",
    subHtml:
      "格式档下，剥掉标记后的正文 token 多重集必须完全一致。删词是 <code>missing</code>，新写措辞是 <code>added</code>，两者都拒绝写回。",
    termAria: "verify 命令输出示例：格式档通过，删词被判硬失败",
    termHtml:
      '<span class="p">$</span> adhd_md.py verify 原文.md 新文.md --scope=format\nscope=format → <span class="ok">通过</span>\n  [警告] blocks_reordered: 检测到块重排，检查悬空指代\n\n<span class="p">$</span> adhd_md.py verify 原文.md 删了一句的.md --scope=format\nscope=format → <span class="bad">失败</span>\n  [硬失败] prose_tokens_missing  count=9\n    items: [生产, 环境, 别, 设成, 0, …]\n    hint: 这些词从正文里消失了。format 档不许删词。',
    grid1: {
      h: "能算准的不交给模型",
      t: "审计、格式修复、无损校验都在一个纯标准库的 Python 单文件里。跑的是同一个进程，不是同一个模型，所以六个宿主的分数与校验结果必然一致。",
    },
    grid2: {
      h: "分数不虚报",
      t: "75 条规则里 44 条脚本可判定（42 条计分、2 条提示），31 条标记为需模型判断。<code>audit</code> 输出的叫「脚本分」，不给「优」档。脚本分低说明一定有问题，脚本分高不说明没问题。",
    },
  },
  hosts: {
    h2: "一份 skill，六个 agent",
    subHtml:
      "六个宿主都原生支持同一套 <code>SKILL.md</code> 目录格式，所以不需要六套适配器。canonical skill 放 <code>~/.agents/skills/</code>，各宿主放软链，改一处同时生效。",
    items: [
      { name: "Claude Code", path: "~/.claude/skills/", badge: "运行时实测", live: true },
      { name: "Codex", path: "~/.codex/skills/", badge: "运行时实测", live: true },
      { name: "Grok Build", path: "~/.grok/skills/", badge: "加载实测", live: false },
      { name: "Gemini CLI", path: "~/.gemini/skills/", badge: "加载实测", live: false },
      { name: "Cursor", path: "~/.cursor/skills/", badge: "加载实测", live: false },
      { name: "opencode", path: "~/.config/opencode/skills/", badge: "加载实测", live: false },
    ],
    note:
      "Codex headless 跑了完整流程，自己发现目标文件有未提交改动，于是改写到旁路文件而没覆盖原文件。这正是 skill 第 0 步的逻辑。产出与手写版本不同，但同样合格。它把两条警告合成引用块，我把配置转成列表，都是 100 分，都零词改动。",
    noteSmall:
      "另外四个宿主只验证了能加载，没验证执行效果。",
    noteLink: "验证结论",
    noteSmallAfter: "里写清了哪些验过、哪些没验、有哪些已知局限。",
  },
  start: {
    h2: "两分钟装好",
    s1: "装。三种方式任选一种，脚本会探测本机装了哪些 agent，只往存在的宿主里放。",
    wayNode: "有 Node",
    wayNoNode: "没 Node",
    waySource: "想改源码",
    noteSmHtml:
      "克隆装的是软链，<code>git pull</code> 即更新。npx 与 curl 装的是复制，重跑一次即更新。",
    s2: "先审一篇看看分数和问题清单。",
    s3: "然后在任意 agent 里直接说人话。",
    quote: "把 README.md 改成 ADHD 友好的，只改格式",
    ciH: "接 CI",
    ciCmd: "adhd_md.py fmt --check docs/*.md\nadhd_md.py audit --min-score 70 docs/*.md",
    noShellH: "没有命令执行能力的环境",
    noShellHtml:
      "网页版 LLM 直接粘贴自包含单文件 <a href=\"https://github.com/tsonglew/adhd-md/blob/main/dist/adhd-md.standalone.md\">adhd-md.standalone.md</a> ，30 KB，规则全带。降级后没有机器校验，报告里必须写明。",
  },
};

const en: typeof zh = {
  lang: "en",
  otherUrl: "/adhd-md/",
  meta: {
    title: "adhd-md — make Markdown readable",
    description:
      "One skill for six agents: turn Markdown into something ADHD-friendly and skimmable. Fix formatting only, content only, or both. Rearrange information, never delete it — format-mode changes are provably lossless.",
    canonical: "https://tsonglew.github.io/adhd-md/en/",
    ogTitle: "adhd-md — make Markdown readable",
    ogDescription:
      "One skill that works in Claude Code, Codex, Grok Build, Gemini CLI, Cursor, and opencode. Rearrange information, never delete it.",
    ogImage: "https://tsonglew.github.io/adhd-md/og-en.png",
    ogImageAlt: "adhd-md: make Markdown readable. Rearrange information, never delete it. Score 87.8 to 100, not a single word changed.",
    twitterTitle: "adhd-md — make Markdown readable",
    twitterDescription:
      "One skill for six agents. Rearrange information, never delete it. Format-mode changes are provably lossless.",
    twitterImageAlt: "adhd-md preview: score 87.8 to 100, not a single word changed.",
  },
  skip: "Skip to content",
  nav: ["Compare", "Three modes", "AI slop", "Lossless", "Hosts"],
  langSwitch: { label: "中文", href: "/adhd-md/" },
  themeToggle: { ariaToDark: "Switch to dark mode", ariaToLight: "Switch to light mode" },
  footer: {
    tagline: "MIT · pure-stdlib Python, zero dependencies",
    links: [
      { label: "Source", href: "https://github.com/tsonglew/adhd-md" },
      { label: "Rules", href: "https://github.com/tsonglew/adhd-md/blob/main/skill/references/rules.md" },
      { label: "Anti-patterns", href: "https://github.com/tsonglew/adhd-md/blob/main/skill/references/antipatterns.md" },
      { label: "Host matrix", href: "https://github.com/tsonglew/adhd-md/blob/main/docs/host-matrix.md" },
      { label: "What we verified", href: "https://github.com/tsonglew/adhd-md/blob/main/docs/eval.md" },
      { label: "Report an issue", href: "https://github.com/tsonglew/adhd-md/issues/new/choose" },
    ],
  },
  hero: {
    eyebrow: "Agent skill · works in six agents",
    h1a: "Make your Markdown",
    h1b: "readable",
    h1c: "",
    lede: "Conclusion first, short chunks, clear next steps. The same skill works in Claude Code, Codex, Grok Build, Gemini CLI, Cursor, and opencode.",
    creed1: "Rearrange information. Never delete it.",
    creed2: "Too long? Collapse it or move it to an appendix. Format-mode changes are provably lossless.",
    buttons: ["Source", "See the demo"],
  },
  problem: {
    h2: "Unreadable docs are usually a layout problem",
    sub: "The same information, unreadable as a blob, readable once it's cut up. Nothing in the content changes.",
    wall:
      "md-cache is a Markdown rendering cache middleware that stores render results on disk keyed by content hash, and returns them directly on hit so nothing renders twice. It requires Node 18+, and its only dependency is lru-cache. Once installed, wrap your rendering pipeline with withCache. The cache directory defaults to .cache/md, and you can change it with the MD_CACHE_DIR environment variable. The default entry limit is 500, changeable via the maxEntries option. The default TTL is 7 days, changeable via the ttl option in milliseconds. Setting it to 0 means never expire, but the disk grows forever, which production environments should avoid.",
    proof: ["Seven things in one paragraph", "conclusion buried at the end"],
    cost: [
      { k: "Back-references", t: "“As mentioned above” makes your eyes go back, relocate, and return. One full working-memory reset, for free" },
      { k: "Buried conclusion", t: "Readers decide in the first 15 lines whether to stay. A conclusion on line 40 might as well not exist" },
      { k: "No next step", t: "You know the theory but not what to type. Startup friction becomes abandonment" },
      { k: "AI slop", t: "“It's not X, it's Y” makes readers load a misconception they never had, then unload it" },
    ],
  },
  compare: {
    h2: "Same document, not a single word changed",
    subHtml:
      "This is real corpus material. <code>scope=format</code> only touches markup, whitespace, and block order — the word sequence stays verbatim. Compare the two sides.",
    beforeTag: "Before",
    afterTag: "After",
    scoreBefore: "87.8",
    scoreAfter: "100",
    docTitle: "md-cache",
    beforeParas: [
      "md-cache is a Markdown rendering cache middleware that stores render results on disk keyed by content hash, and returns them directly on hit so nothing renders twice. It requires Node 18+, and its only dependency is lru-cache. Once installed, wrap your rendering pipeline with withCache. The cache directory defaults to .cache/md, and you can change it with the MD_CACHE_DIR environment variable. The default entry limit is 500, changeable via the maxEntries option. The default TTL is 7 days, changeable via the ttl option in milliseconds. Setting it to 0 means never expire, but the disk grows forever, which production environments should avoid.",
      "If your render function has side effects, don't use this middleware, because on a cache hit the render function never runs. If your Markdown embeds timestamps or random values, the output gets frozen by the cache and looks like it never refreshes. That's not a bug.",
      "Measured on a site with 1,200 documents: cold build 42 seconds, second build 3.1 seconds. Thirteen times faster.",
    ],
    after: {
      moved: "Measured on a site with 1,200 documents: cold build 42 seconds, second build 3.1 seconds. Thirteen times faster.",
      p1: "md-cache is a Markdown rendering cache middleware that stores render results on disk keyed by content hash, and returns them directly on hit so nothing renders twice.",
      p2Html:
        "It requires Node 18+, and its only dependency is <code>lru-cache</code>. Once installed, wrap your rendering pipeline with <code>withCache</code>.",
      list: [
        "The cache directory defaults to <code>.cache/md</code>, changeable via the <code>MD_CACHE_DIR</code> environment variable.",
        "The default entry limit is 500, changeable via the <code>maxEntries</code> option.",
        "The default TTL is 7 days, changeable via the <code>ttl</code> option, in milliseconds.",
        "Setting it to <code>0</code> means never expire, but the disk grows forever. Avoid in production.",
      ],
      p3: "If your render function has side effects, don't use this middleware, because on a cache hit the render function never runs.",
      p4: "If your Markdown embeds timestamps or random values, the output gets frozen by the cache and looks like it never refreshes. That's not a bug.",
    },
    dims: [
      { before: 40, after: 100, label: "Conclusion first" },
      { before: 92, after: 100, label: "Chunking" },
      { before: 100, after: 100, label: "Scannability" },
      { before: 100, after: 100, label: "Sentence load" },
      { before: 100, after: 100, label: "Actionability" },
      { before: 100, after: 100, label: "Consistency" },
      { before: 100, after: 100, label: "Human voice" },
    ],
    footChanged: "Changed: moved the conclusion up, split one blob into four paragraphs, turned four config sentences into a list, wrapped bare identifiers in code.",
    footWords: "Words added: 0. Words deleted: 0.",
    asideHtml:
      "Notice what the fixed version doesn't do: no heading above the config list. The word “Configuration” isn't in the original — adding it would be new wording, which crosses into <code>content</code>. You can restructure everything, but you can't touch a single word. That's the ceiling of format mode, and it's the point.",
  },
  scope: {
    h2: "Format only, content only, or both",
    sub: "One line draws the boundary. Moving an existing block is format. Writing a new sentence is content.",
    cards: [
      {
        name: "format",
        lede: "The word sequence stays verbatim. Only markup, whitespace, and block order change.",
        can: "Can do",
        canText: "Split paragraphs at existing sentence breaks · turn parallel sentences into lists (reusing the words) · bold existing terms · reorder blocks · add code fence language tags · collapse sections · fix CJK spacing and punctuation",
        cant: "Can't do",
        cantText: "Change a single word · write a new TL;DR · reword headings",
        seal: "Provably lossless",
      },
      {
        name: "content",
        lede: "Only wording and information structure change. Layout stays untouched.",
        can: "Can do",
        canText: "Split long sentences · passive to active · write a TL;DR · conclusion-style headings · add time estimates and next steps · explain terms on first use · cut filler",
        cant: "Can't do",
        cantText: "Touch layout · delete constraints, units, versions, or edge cases in the name of “tightening”",
        seal: "Invariants preserved",
      },
      {
        name: "both",
        tag: "default",
        lede: "Content first, then format, then one combined check.",
        can: "The other axis",
        canTextHtml:
          "<code>light</code> does zero-risk fixes only, for specs and API docs. <code>standard</code> splits, lists, retitles, and writes a TL;DR. <code>deep</code> rebuilds the whole skeleton, for meeting notes and messy drafts.",
        cant: "How to use it",
        cantText: "Just say it in plain words: “Make README.md ADHD-friendly, format only”",
        seal: "75 rules filtered by axis and level",
      },
    ],
  },
  human: {
    h2: "While it's here, it also strips AI slop",
    sub: "Model-written Chinese has a fixed set of routines. Each one costs the reader an extra bit of attention, so they belong to this skill.",
    taxHead: ["Routine", "Attention the reader pays"],
    tax: [
      { a: "It's not X. It's Y.", b: "Load a misconception you never had, then unload it. One working-memory reset, for free" },
      { a: "The core is:", b: "Announces importance before delivering the goods — the sentence says itself twice" },
      { a: "It's worth noting", b: "Promises depth, delivers none. One attention unit, stolen" },
      { a: "Completed an optimization of…", b: "The verb hides inside a noun. One extra parse to find out who did what" },
      { a: "leverage, synergy, end-to-end", b: "Plain words carry the same information, minus the translation step" },
      { a: "Time will keep the details", b: "No subject to hold accountable. Nothing to verify" },
      { a: "extensive tests, various scenarios", b: "Quantities without numbers carry no information" },
      { a: "significantly better, fully solves", b: "No number, nothing to verify" },
    ],
    grid1: {
      h: "Em dashes aren't banned. Their density is.",
      html: "An <code>—</code> is a normal piece of punctuation, fine for a parenthetical. The tell is using it as a rhythm crutch. Hand-written tech docs average about 5 per 1,000 characters; model output often runs above 15. Threshold: 8. And only prose counts — <code>item — owner — due</code> inside list items is field separation, not rhythm.",
    },
    grid2: {
      h: "What a regex can't tell, a model judges",
      html: "Three flags in parallel is good writing. “Why we left, why we failed, why we still try” is what needs fixing. A regex can't tell them apart, so anaphora and metaphor are flagged for review, not docked points. <code>git repo</code> is literal; “a repository of memories” is packaging.",
    },
  },
  lossless: {
    h2: "Delete one word and it gets rejected",
    subHtml:
      "In format mode, the token multiset of the prose, with markup stripped, must match exactly. A missing token is <code>missing</code>, new wording is <code>added</code> — both refuse to write back.",
    termAria: "verify command output example: format mode passes, deleting a sentence fails hard",
    termHtml:
      '<span class="p">$</span> adhd_md.py verify before.md after.md --scope=format\nscope=format → <span class="ok">passed</span>\n  [warning] blocks_reordered: blocks moved, check for dangling references\n\n<span class="p">$</span> adhd_md.py verify before.md missing-a-sentence.md --scope=format\nscope=format → <span class="bad">failed</span>\n  [hard-fail] prose_tokens_missing  count=9\n    items: [production, do, not, set, 0, …]\n    hint: these words vanished from the prose. format mode forbids deletions.',
    grid1: {
      h: "What's computable never goes to a model",
      t: "Audit, format fixes, and lossless verification all live in one pure-stdlib Python file. Same process, not same model — so the scores and checks come out identical across all six hosts.",
    },
    grid2: {
      h: "Scores don't inflate themselves",
      t: "Of the 75 rules, 44 are script-checkable (42 score, 2 advisory) and 31 need model judgment. <code>audit</code> prints a “script score” and never a grade. A low script score always means problems; a high one doesn't always mean none.",
    },
  },
  hosts: {
    h2: "One skill, six agents",
    subHtml:
      "All six hosts natively support the same <code>SKILL.md</code> directory format, so there's nothing to adapt. The canonical skill lives in <code>~/.agents/skills/</code>, each host gets a symlink — change it once, it changes everywhere.",
    items: [
      { name: "Claude Code", path: "~/.claude/skills/", badge: "tested at runtime", live: true },
      { name: "Codex", path: "~/.codex/skills/", badge: "tested at runtime", live: true },
      { name: "Grok Build", path: "~/.grok/skills/", badge: "tested for loading", live: false },
      { name: "Gemini CLI", path: "~/.gemini/skills/", badge: "tested for loading", live: false },
      { name: "Cursor", path: "~/.cursor/skills/", badge: "tested for loading", live: false },
      { name: "opencode", path: "~/.config/opencode/skills/", badge: "tested for loading", live: false },
    ],
    note:
      "Codex ran the whole workflow headless, noticed the target file had uncommitted changes, and wrote to a side file instead of overwriting it — exactly what step 0 of the skill says. Its output differs from my hand-written example, but passes just the same. It merged two warnings into one blockquote; I turned the config into a list. Both scored 100, both changed zero words.",
    noteSmall:
      "The other four hosts are only verified to load the skill, not to run it well.",
    noteLink: "Verification notes",
    noteSmallAfter: "list what's been checked, what hasn't, and the known limits.",
  },
  start: {
    h2: "Installed in two minutes",
    s1: "Install. Any of the three ways works — the script detects which agents you have and only touches those hosts.",
    wayNode: "With Node",
    wayNoNode: "Without Node",
    waySource: "To hack on the source",
    noteSmHtml:
      "The git-clone install is a symlink — <code>git pull</code> updates it. The npx and curl installs copy the skill — rerun to update.",
    s2: "Audit something first and see the score and the findings list.",
    s3: "Then just say it in plain words to any agent.",
    quote: "Make README.md ADHD-friendly, format only",
    ciH: "CI",
    ciCmd: "adhd_md.py fmt --check docs/*.md\nadhd_md.py audit --min-score 70 docs/*.md",
    noShellH: "No command execution available",
    noShellHtml:
      "Web-chat LLMs can paste the self-contained single file, <a href=\"https://github.com/tsonglew/adhd-md/blob/main/dist/adhd-md.standalone.md\">adhd-md.standalone.md</a>, 30 KB with all rules. The catch: no machine checks — say so in your report.",
  },
};

export const ui = { zh, en };
export type UI = typeof zh;
