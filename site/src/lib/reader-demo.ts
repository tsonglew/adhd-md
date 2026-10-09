import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

/** Build the public example with the same generator shipped to skill users. */
export function buildReaderDemo(source: string, sourceName: string): string {
  const scriptDirectory = resolve(process.cwd(), "../skill/scripts");
  const program = [
    "import sys",
    "sys.path.insert(0, sys.argv[1])",
    "from reader import build_reading_data, render_reader",
    "source = sys.stdin.buffer.read().decode('utf-8')",
    // Keep this short sample spread across reading steps; use the real chunker.
    "chunk_size = max(len(part) for part in source.split('\\n\\n') if part.strip()) + 2",
    "sys.stdout.buffer.write(render_reader(build_reading_data(source, sys.argv[2], chunk_size)).encode('utf-8'))",
  ].join("\n");
  return execFileSync("python3", ["-c", program, scriptDirectory, sourceName], {
    input: source,
    encoding: "utf8",
    maxBuffer: 4 * 1024 * 1024,
  });
}
