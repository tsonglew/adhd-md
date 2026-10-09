import { ui } from "../../i18n/ui";
import { buildReaderDemo } from "../../lib/reader-demo";

export const prerender = true;

export function GET() {
  return new Response(buildReaderDemo(ui.en.reading.sourceMarkdown, "md-cache.md"), {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}
