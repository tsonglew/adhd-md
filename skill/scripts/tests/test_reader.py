"""Preservation and safety regressions for the offline reading data layer."""
import hashlib
import importlib.util
import json
import random
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


_SRC = Path(__file__).resolve().parents[1] / "reader.py"
_spec = importlib.util.spec_from_file_location("reader", _SRC)
reader = importlib.util.module_from_spec(_spec)
sys.modules["reader"] = reader
_spec.loader.exec_module(reader)


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.links = []
        self.data = []
        self.json = []
        self.in_json = False

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs)
        if tag == "script" and attrs.get("type") == "application/json":
            self.in_json = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_json = False

    def handle_data(self, data):
        self.data.append(data)
        if self.in_json:
            self.json.append(data)


class ReaderTest(unittest.TestCase):
    def build(self, source, size=90, name="source.md"):
        data = reader.build_reading_data(source, name, size)
        self.assertEqual(data["source_text"], source)
        self.assertEqual("".join(chunk["source"] for chunk in data["chunks"]), source)
        self.assertEqual(data["source_hash"], hashlib.sha256(source.encode("utf-8")).hexdigest())
        self.assertEqual([chunk["index"] for chunk in data["chunks"]], list(range(len(data["chunks"]))))
        return data

    def rendered(self, data):
        parser = _HTML()
        parser.feed("\n".join(chunk["html"] for chunk in data["chunks"]))
        return parser

    def test_preserves_every_character_of_mixed_source(self):
        self.build(
            '\ufeff---\r\ntitle: "不要丢元信息"\r\n---\r\n\r\n# 文件标题\r\n\r\n'
            '正文有 emoji 🧠、英文 API_KEY 和软\r\n换行。这里还有下一句。\r\n\r\n'
            '- first\r\n  - nested\r\n\r\n- second\r\n\r\n'
            '| 名称 | 内容 |\r\n| --- | --- |\r\n| a | b |\r\n\r\n'
            '```html\r\n<script>doNotRun()</script>\r\n\r\n```\r\n\r\n'
            '<details><summary>原始 HTML</summary>仍保留</details>\r\n\r\n  ', 30
        )

    def test_empty_and_whitespace_sources_are_lossless(self):
        self.assertEqual(self.build("")["chunks"], [])
        for source in (" ", "\n\n", " \r\n\t\r\n"):
            data = self.build(source)
            self.assertEqual(len(data["chunks"]), 1)
            self.assertEqual(data["chunks"][0]["start_line"], 1)

    def test_line_numbers_include_newline_on_previous_line(self):
        data = self.build("# One\r\n\r\nBody.\r\n\r\n## Two\r\nSecond body.\r\n", 1000)
        self.assertEqual([(chunk["start_line"], chunk["end_line"]) for chunk in data["chunks"]], [(1, 4), (5, 6)])

    def test_line_numbers_can_overlap_for_same_line_sentences(self):
        data = self.build("First sentence. Second sentence. Third sentence.\n", 20)
        self.assertEqual(len(data["chunks"]), 3)
        self.assertTrue(all(chunk["start_line"] == chunk["end_line"] == 1 for chunk in data["chunks"]))

    def test_heading_title_and_section_context(self):
        data = self.build("# **Readable** `API_KEY`\n\nOne.\n\n## Next\n\nTwo. More.\n", 1000)
        self.assertEqual(data["title"], "Readable API_KEY")
        self.assertEqual([chunk["title"] for chunk in data["chunks"]], ["Readable API_KEY", "Next"])

    def test_setext_heading_and_filename_fallback(self):
        self.assertEqual(self.build("Plain title\n===========\n\nBody")["title"], "Plain title")
        self.assertEqual(self.build("Body only", name="/documents/会议记录.md")["title"], "会议记录")

    def test_heading_stays_with_following_long_paragraph(self):
        source = "# Context\n\n" + "长句不能从中间断开" * 20 + "。"
        data = self.build(source, 40)
        self.assertEqual(len(data["chunks"]), 1)

    def test_long_paragraph_splits_only_at_sentences(self):
        source = "第一句内容比较短。第二句内容也比较短。第三句完整保留。"
        data = self.build(source, 12)
        self.assertGreater(len(data["chunks"]), 1)
        self.assertTrue(all(chunk["source"].endswith("。") for chunk in data["chunks"]))

    def test_long_unbroken_sentence_is_a_soft_limit(self):
        self.assertEqual(len(self.build("x" * 3000, 100)["chunks"]), 1)

    def test_sentence_split_keeps_inline_spans_intact(self):
        code = "`first sentence. second sentence.`"
        strong = "**first sentence. second sentence.**"
        link = "[first sentence. second sentence.](https://example.com)"
        for span in (code, strong, link):
            data = self.build("Before. " + span + " After.", 12)
            self.assertTrue(any(span in chunk["source"] for chunk in data["chunks"]))

    def test_fences_remain_whole_even_with_inner_shorter_fences(self):
        block = "````md\n# not a title\n\n```js\nalert('x')\n```\n````\n"
        data = self.build("Before.\n\n" + block + "\nAfter.\n", 10)
        self.assertTrue(any(block in chunk["source"] for chunk in data["chunks"]))
        parsed = self.rendered(data)
        self.assertIn("pre", parsed.tags)
        self.assertNotIn("h1", parsed.tags)

    def test_unclosed_fence_keeps_all_remaining_source(self):
        block = "~~~text\n# code\n\nStill code.\n"
        data = self.build(block, 5)
        self.assertEqual(len(data["chunks"]), 1)
        self.assertIn("Still code.", "".join(self.rendered(data).data))

    def test_frontmatter_preserved_and_not_used_as_title(self):
        source = "---\ntitle: metadata\nkey: value\n---\n\n# Visible title\n\nContent."
        data = self.build(source, 15)
        self.assertEqual(data["title"], "Visible title")
        self.assertTrue(any("title: metadata\nkey: value" in chunk["source"] for chunk in data["chunks"]))
        self.assertIn("key: value", "".join(self.rendered(data).data))

    def test_table_stays_whole_and_renders_cells(self):
        block = "| Label | Value |\n| :--- | ---: |\n| A | `1` |\n| B | 2 |\n"
        data = self.build("Start.\n\n" + block + "\nEnd.", 15)
        self.assertTrue(any(block in chunk["source"] for chunk in data["chunks"]))
        parsed = self.rendered(data)
        self.assertIn("table", parsed.tags)
        self.assertEqual(parsed.tags.count("th"), 2)
        self.assertEqual(parsed.tags.count("td"), 4)

    def test_list_and_nested_items_stay_whole(self):
        block = "3. First\n   - nested one\n   - nested two\n\n4. Second\n   continuation\n"
        data = self.build("Start.\n\n" + block + "\nEnd.\n", 15)
        self.assertTrue(any(block in chunk["source"] for chunk in data["chunks"]))
        parsed = self.rendered(data)
        self.assertIn("ol", parsed.tags)
        self.assertIn("ul", parsed.tags)
        self.assertEqual(parsed.tags.count("li"), 4)
        self.assertIn("continuation", "".join(parsed.data))

    def test_ordered_list_retains_explicit_item_numbers(self):
        data = self.build("1. First\n3. Third\n9. Ninth\n")
        rendered = data["chunks"][0]["html"]
        self.assertIn('<li value="1">', rendered)
        self.assertIn('<li value="3">', rendered)
        self.assertIn('<li value="9">', rendered)

    def test_indented_code_and_quote_render_without_data_loss(self):
        data = self.build("    <code>& value\n    second\n\n> Quote **bold**\n> continued\n", 15)
        parsed = self.rendered(data)
        self.assertIn("blockquote", parsed.tags)
        self.assertIn("strong", parsed.tags)
        self.assertIn("<code>& value", "".join(parsed.data))

    def test_raw_html_is_always_visible_text(self):
        source = '<script>alert(1)</script>\n<img src="https://example.com/a" onerror="boom()">\n<iframe src="https://example.com"></iframe>'
        parsed = self.rendered(self.build(source))
        for tag in ("script", "img", "iframe"):
            self.assertNotIn(tag, parsed.tags)
        self.assertIn(source, "".join(parsed.data))

    def test_unsafe_link_schemes_are_nonclickable(self):
        urls = ["javascript:alert(1)", "data:text/html,bad", "file:///etc/passwd", "vbscript:msgbox(1)", "jav&#x61;script:alert(1)", "//example.com", "relative.md", "#original-section"]
        for url in urls:
            with self.subTest(url=url):
                parsed = self.rendered(self.build("[visible label](" + url + ")"))
                self.assertEqual(parsed.links, [])
                self.assertIn("visible label", "".join(parsed.data))

    def test_safe_links_use_escaped_attributes_and_safe_rel(self):
        source = '[A](https://example.com/?a=1&b=2) [mail](mailto:test@example.com) <https://example.org>'
        parsed = self.rendered(self.build(source))
        self.assertEqual(len(parsed.links), 3)
        self.assertEqual(parsed.links[0]["href"], "https://example.com/?a=1&b=2")
        self.assertTrue(all(link["rel"] == "noopener noreferrer" for link in parsed.links))

    def test_link_attribute_breakout_cannot_create_handler(self):
        parsed = self.rendered(self.build('[x](https://example.com/"onmouseover="attack)'))
        self.assertEqual(len(parsed.links), 1)
        self.assertNotIn("onmouseover", parsed.links[0])

    def test_markdown_images_never_load_automatically(self):
        parsed = self.rendered(self.build("![远程图片](https://example.com/track.png) ![bad](javascript:alert(1))"))
        self.assertNotIn("img", parsed.tags)
        self.assertEqual(len(parsed.links), 1)
        self.assertIn("远程图片", "".join(parsed.data))

    def test_plain_text_does_not_interpret_markdown(self):
        source = '# Literal heading\n\n*literal stars* [literal link](https://example.com)\n<script>x</script>'
        data = self.build(source, name="/tmp/notes.txt")
        parsed = self.rendered(data)
        self.assertEqual(data["title"], "notes")
        self.assertNotIn("h1", parsed.tags)
        self.assertNotIn("em", parsed.tags)
        self.assertNotIn("a", parsed.tags)
        self.assertNotIn("script", parsed.tags)
        self.assertEqual("".join(chunk["source"] for chunk in data["chunks"]), source)
        self.assertTrue(all('class="reader-plain"' in chunk["html"] for chunk in data["chunks"]))

    def test_json_cannot_break_out_of_template_script(self):
        source = '</script><script>alert("bad")</script>&\u2028\u2029'
        data = self.build(source, name='</script><img src=x>.md')
        page = reader.render_reader(data)
        parsed = _HTML()
        parsed.feed(page)
        payload = "".join(parsed.json)
        self.assertEqual(json.loads(payload), data)
        self.assertNotIn("<", payload)
        self.assertNotIn(">", payload)
        self.assertNotIn("&", payload)
        self.assertNotIn("\u2028", payload)
        self.assertNotIn("\u2029", payload)
        self.assertNotIn("__ADHD_READER_DATA__", page)

    def test_nonpositive_chunk_size_is_rejected(self):
        for size in (0, -1, True, 1.5, "90"):
            with self.subTest(size=size), self.assertRaises(ValueError):
                reader.build_reading_data("text", "test.md", size)

    def test_random_mixed_documents_always_partition_exact_source(self):
        randomizer = random.Random(2026)
        snippets = ["\n", " \r\n", "# Heading\n", "普通正文。下一句。\n", "```\ncode\n```\n", "- item\n  continued\n", "| A |\n| --- |\n| B |\n", "<raw>& data\n", "\tindented\n", "---\n", "[x](javascript:alert(1))\n"]
        for _ in range(40):
            source = "".join(randomizer.choice(snippets) for _ in range(20))
            self.build(source, randomizer.choice([1, 20, 90, 900]))


if __name__ == "__main__":
    unittest.main()
