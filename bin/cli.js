#!/usr/bin/env node
"use strict";

/**
 * adhd-md 的 npx 入口。
 *
 * 两件事：把 skill 装到本机各 agent 宿主，或者直接跑确定性工具层。
 * 本身零依赖，只做参数分派与前置检查 —— 真正的活在 scripts/install.sh
 * 和 skill/scripts/adhd_md.py 里。
 */

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const PKG = require(path.join(ROOT, "package.json"));

const TOOL_CMDS = ["audit", "fmt", "verify", "report", "init", "selftest"];

/**
 * 帮助里该印哪种调用方式。
 *
 * 这个包不发布到 npm registry，所以不能印 `npx adhd-md` —— 照着敲会 404。
 * 现实里只有两种跑法：npx 从 GitHub 拉，或者克隆下来直接 node 跑。
 */
function invocation() {
  const p = process.argv[1] || "";
  if (p.includes("_npx")) return "npx github:tsonglew/adhd-md";
  if (p.includes("node_modules")) return "npx adhd-md";
  return "node bin/cli.js";
}

const X = invocation();

const USAGE = `adhd-md ${PKG.version} — 把 Markdown 改造成 ADHD 友好、可扫读的版本

安装到 agent 宿主
  ${X}                        装到本机所有支持 SKILL.md 的宿主
  ${X} install --project      只装到当前仓库
  ${X} install --uninstall    卸载
  ${X} install --dry-run      只打印会做什么

直接用工具层
  ${X} audit  文档.md                          审计并打分
  ${X} fmt    文档.md --write                  确定性格式修复
  ${X} verify 原文.md 新文.md --scope=format   无损校验
  ${X} report 原文.md 新文.md                  改前改后对比
  ${X} init --type=readme                      生成文档骨架
  ${X} selftest                                自检

装好之后，在任意 agent 里直接说人话即可：
  「把 README.md 改成 ADHD 友好的，只改格式」

文档  https://tsonglew.github.io/adhd-md/`;

function die(msg, code = 1) {
  console.error(msg);
  process.exit(code);
}

/** 找一个能用的 python3。工具层只依赖标准库，版本要求 3.9+ */
function resolvePython() {
  for (const bin of ["python3", "python"]) {
    const r = spawnSync(bin, ["-c", "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"], {
      stdio: "ignore",
    });
    if (r.status === 0) return bin;
  }
  return null;
}

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd: process.cwd() });
  if (r.error) die(`跑不起来 ${cmd}：${r.error.message}`);
  process.exit(r.status === null ? 1 : r.status);
}

function doInstall(args) {
  if (process.platform === "win32") {
    die(
      [
        "安装脚本需要 bash，Windows 下请在 WSL 或 Git Bash 里跑：",
        "  bash scripts/install.sh",
        "",
        "或者手动把 skill 目录拷到宿主的 skills 目录，参考：",
        "  https://github.com/tsonglew/adhd-md/blob/main/docs/host-matrix.md",
      ].join("\n")
    );
  }

  const script = path.join(ROOT, "scripts", "install.sh");
  if (!fs.existsSync(script)) die(`找不到安装脚本：${script}`);

  // npx 把包解到临时缓存目录，缓存会被清理。
  // 所以默认必须是「复制」而不是「软链」—— 软链到缓存目录早晚变成死链。
  const wantsLink = args.includes("--link");
  const finalArgs = wantsLink
    ? args.filter((a) => a !== "--link")
    : args.includes("--copy")
      ? args
      : ["--copy", ...args];

  run("bash", [script, ...finalArgs]);
}

function doTool(argv) {
  const py = resolvePython();
  if (!py) {
    die(
      [
        "需要 Python 3.9 以上（工具层只用标准库，不装任何依赖）。",
        "  macOS   xcode-select --install",
        "  Debian  sudo apt install python3",
      ].join("\n")
    );
  }
  const tool = path.join(ROOT, "skill", "scripts", "adhd_md.py");
  if (!fs.existsSync(tool)) die(`找不到工具层：${tool}`);
  run(py, [tool, ...argv]);
}

function main() {
  const argv = process.argv.slice(2);
  const first = argv[0];

  if (!first || first === "install") return doInstall(argv.slice(first ? 1 : 0));
  if (first === "-h" || first === "--help" || first === "help") return console.log(USAGE);
  if (first === "-v" || first === "--version") return console.log(PKG.version);
  if (TOOL_CMDS.includes(first)) return doTool(argv);

  // 光给个文件名也认，默认当安装还是审计容易猜错，这里明确提示
  if (fs.existsSync(first)) {
    die(`要审计就写清楚：npx adhd-md audit ${first}\n要安装就直接 npx adhd-md`, 2);
  }
  die(`不认识的命令：${first}\n\n${USAGE}`, 2);
}

main();
