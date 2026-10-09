"""Exercise HTML preservation and bounded fetching without an external service."""
from email.message import Message
import io
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract_web


class HTMLExtractionTest(unittest.TestCase):
    def extract(self, text, location="https://example.org/docs/start"):
        return extract_web.extract_html(text, location)

    def test_main_is_first_and_all_other_visible_text_survives(self):
        html = """<title>阅读与注意力</title><body><nav>网站导航</nav>
        <main><h1>文档题目</h1><article><p>第一段。</p><p>第二段。</p></article></main>
        <aside>限定条件不应丢失</aside><footer>版权说明</footer></body>"""
        data = self.extract(html)
        text = data["text"]
        self.assertTrue(text.startswith("# 文档题目"))
        self.assertLess(text.index("第二段"), text.index("网站导航"))
        for phrase in ("网站导航", "第一段", "第二段", "限定条件不应丢失", "版权说明"):
            self.assertEqual(text.count(phrase), 1)
        self.assertIn("附录", text)
        self.assertEqual(data["origin"]["original_html"], html)
        self.assertEqual(data["origin"]["kind"], "web")
        self.assertEqual(data["source_name"], "阅读与注意力.md")

    def test_multiple_articles_and_nested_wrappers_do_not_duplicate(self):
        text = self.extract("<body>intro<article><div><article><p>first</p></article></div></article><article>second</article>end</body>")["text"]
        for value in ("intro", "first", "second", "end"):
            self.assertEqual(text.count(value), 1)
        self.assertLess(text.index("second"), text.index("intro"))

    def test_hidden_elements_removed_from_reading_but_original_retained(self):
        html = """<head><title>标题</title><script>head_secret</script></head>
        <main>visible<script>script_secret</script><style>style_secret</style>
        <template>template_secret</template><p hidden>hidden_secret</p>
        <div style="display: none !important">display_secret</div>
        <span style="visibility:hidden">invisible_secret</span><p>end</p></main>"""
        data = self.extract(html)
        for word in ("head_secret", "script_secret", "style_secret", "template_secret", "hidden_secret", "display_secret", "invisible_secret"):
            self.assertNotIn(word, data["text"])
            self.assertIn(word, data["origin"]["original_html"])
        self.assertIn("visible", data["text"])
        self.assertIn("end", data["text"])

    def test_chinese_inline_spans_and_english_spaces(self):
        text = self.extract("<main><p>先<span>阅读</span>这一段。</p><p>Hello <span>careful</span> reader.</p><p>A<br>B</p></main>")["text"]
        self.assertIn("先阅读这一段。", text)
        self.assertIn("Hello careful reader.", text)
        self.assertIn("A  \nB", text)
        self.assertNotIn("这一段。Hello", text)

    def test_inline_formatting_preserves_surrounding_spaces(self):
        text = self.extract('<main>Hello<strong> careful </strong>reader. Use<a href="/guide"> this guide </a>today.</main>')["text"]
        self.assertIn("Hello **careful** reader.", text)
        self.assertIn("Use [this guide](https://example.org/guide) today.", text)

    def test_malformed_content_outside_body_is_retained(self):
        text = self.extract("<title>Metadata</title>before<body><main>main content</main></body>after<body>extra body</body>")["text"]
        for value in ("before", "main content", "after", "extra body"):
            self.assertEqual(text.count(value), 1)
        self.assertNotIn("Metadata", text)

    def test_optional_head_end_tag_does_not_hide_the_body(self):
        for markup in (
            "<html><head><title>Article</title><body><main><p>Actual body</p></main></body></html>",
            "<html><head><title>Article</title><main><p>Actual body</p></main></html>",
            "<html><head><title>Article</title><p>Actual body</p></html>",
        ):
            with self.subTest(markup=markup):
                data = self.extract(markup)
                self.assertEqual(data["title"], "Article")
                self.assertEqual(data["text"].count("Actual body"), 1)

    def test_template_content_in_head_does_not_become_visible(self):
        data = self.extract("<head><title>Article</title><template><div>hidden</div></template><body><main>Visible</main></body>")
        self.assertIn("Visible", data["text"])
        self.assertNotIn("hidden", data["text"])

    def test_reversed_numbered_lists_preserve_start_and_item_values(self):
        data = self.extract('<main><ol reversed start="3"><li>Third<li>Second<li>First</ol></main>')["text"]
        self.assertIn("3. Third\n2. Second\n1. First", data)
        data = self.extract('<main><ol reversed><li>Third<li>Second<li>First</ol></main>')["text"]
        self.assertIn("3. Third\n2. Second\n1. First", data)
        data = self.extract('<main><ol reversed start="9"><li>Nine<li value="5">Five<li>Four</ol></main>')["text"]
        self.assertIn("9. Nine\n5. Five\n4. Four", data)

    def test_superscript_and_subscript_do_not_concatenate_numbers(self):
        text = self.extract("<main><p>2<sup>3</sup> = 8; H<sub>2</sub>O; x<sup> n + 1 </sup>end.</p></main>")["text"]
        self.assertIn("2^(3) = 8", text)
        self.assertIn("H_(2)O", text)
        self.assertIn("x ^(n + 1) end.", text)

    def test_lists_quotes_tables_and_preformatted_code(self):
        text = self.extract("""<main><ol start="3"><li>第三项<li value="7">第七项<ul><li>子项</li></ul></ol>
        <blockquote><p>引文 A</p><p>引文 B</p></blockquote>
        <table><caption>表格说明</caption><thead><tr><th>名字</th><th>值</th></tr></thead>
        <tbody><tr><td>甲</td><td>1 | 2</td></tr></tbody><tfoot><tr><td>总计</td><td>3</td></tr></tfoot></table>
        <pre><code>  x = 1\n\n\n  print(x)\n```</code></pre></main>""")["text"]
        self.assertIn("3. 第三项", text)
        self.assertIn("7. 第七项", text)
        self.assertEqual(text.count("子项"), 1)
        self.assertIn("> 引文 A", text)
        self.assertIn("> 引文 B", text)
        self.assertIn("表格说明", text)
        self.assertIn("| 名字 | 值 |", text)
        self.assertIn("| 甲 | 1 \\| 2 |", text)
        self.assertIn("| 总计 | 3 |", text)
        self.assertIn("````\n  x = 1\n\n\n  print(x)\n```\n````", text)

    def test_malformed_html_retains_omitted_end_tag_content(self):
        text = self.extract("<main><h1>Title<p>one<p>two<ul><li>three<li>four</ul><table><tr><td>five<td>six<tr><td>seven<td>eight</main>")["text"]
        for word in ("Title", "one", "two", "three", "four", "five", "six", "seven", "eight"):
            self.assertEqual(text.count(word), 1)
        self.assertIn("| five | six |", text)
        self.assertIn("| seven | eight |", text)

    def test_relative_links_base_fragments_and_image_sources(self):
        data = self.extract("""<head><base href="/reference/"></head><main><p><a href="guide?q=1#细节">指南</a></p>
        <img src="../chart.png" alt="流程图"><a href="mailto:reader@example.org">邮箱</a></main>""")
        self.assertIn("[指南](https://example.org/reference/guide?q=1#%E7%BB%86%E8%8A%82)", data["text"])
        self.assertIn("[流程图](https://example.org/chart.png)", data["text"])
        self.assertIn("[邮箱](mailto:reader@example.org)", data["text"])
        self.assertTrue(any("图片" in warning for warning in data["origin"]["warnings"]))

    def test_unsafe_links_keep_text_and_do_not_become_destinations(self):
        data = self.extract("""<main><a href="jav&#97;script:alert(1)">按钮文字</a>
        <a href="data:text/html,content">下载</a><a href="https://user:secret@example.org/a">私有链接</a>
        <a href="https://example.org/a)b( c">复杂地址</a></main>""")
        for value in ("按钮文字", "下载", "私有链接", "复杂地址"):
            self.assertIn(value, data["text"])
        self.assertNotIn("javascript:", data["text"])
        self.assertNotIn("data:text", data["text"])
        self.assertNotIn("secret", data["text"])
        self.assertIn("https://example.org/a%29b%28%20c", data["text"])
        self.assertTrue(data["origin"]["warnings"])

    def test_local_html_unknown_tags_and_safe_filename(self):
        data = self.extract('<title>../../a:b?c</title><body><custom-element>one</custom-element><div>two</div></body>', "/tmp/page.html")
        self.assertEqual(data["origin"]["kind"], "html")
        self.assertEqual(data["origin"]["location"], "/tmp/page.html")
        self.assertNotIn("/", data["source_name"])
        self.assertNotIn(":", data["source_name"])
        self.assertIn("one", data["text"])
        self.assertIn("two", data["text"])
        self.assertTrue(any("main/article" in warning for warning in data["origin"]["warnings"]))

    def test_empty_and_javascript_shell_give_actionable_error(self):
        for html in ("", "<html><head><title>app</title></head><body><div id='root'></div><script>runApp()</script></body></html>"):
            with self.subTest(html=html), self.assertRaisesRegex(ValueError, "JavaScript|正文"):
                self.extract(html)

    def test_decode_utf8_utf16_header_meta_and_chinese_fallback(self):
        source = "<main>阅读已有内容。</main>"
        self.assertEqual(extract_web.decode_html(source.encode("utf-8")), source)
        self.assertEqual(extract_web.decode_html(source.encode("utf-16")), source)
        self.assertEqual(extract_web.decode_html(source.encode("gbk"), "gb2312"), source)
        tagged = '<meta charset="gb2312">' + source
        self.assertEqual(extract_web.decode_html(tagged.encode("gbk")), tagged)
        tagged = '<meta http-equiv="Content-Type" content="text/html; charset=big5">繁體中文'
        self.assertEqual(extract_web.decode_html(tagged.encode("big5")), tagged)
        self.assertEqual(extract_web.decode_html(source.encode("gbk")), source)

    def test_decode_never_replaces_invalid_bytes_or_accepts_null(self):
        for value in (b"\xff", b"<p>\xff</p>", b"<p>\x00</p>", b""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                extract_web.decode_html(value)


class _Response(io.BytesIO):
    def __init__(self, body=b"<p>body</p>", url="https://example.org/final", headers=None):
        super().__init__(body)
        self.url = url
        self.headers = Message()
        for key, value in ({"Content-Type": "text/html; charset=utf-8"} if headers is None else headers).items():
            self.headers[key] = value

    def geturl(self):
        return self.url


class FetchURLTest(unittest.TestCase):
    def fetch_mock(self, response, **kwargs):
        opener = Mock()
        opener.open.return_value = response
        with patch.object(extract_web, "build_opener", return_value=opener):
            result = extract_web.fetch_url("https://example.org/start", **kwargs)
        return result, opener

    def test_fetch_returns_bytes_metadata_and_final_location(self):
        data, opener = self.fetch_mock(_Response())
        self.assertEqual(data["body"], b"<p>body</p>")
        self.assertEqual(data["url"], "https://example.org/final")
        self.assertEqual(data["content_type"], "text/html")
        self.assertEqual(data["charset"], "utf-8")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header("Accept-encoding"), "identity")
        self.assertIsNone(request.get_header("Cookie"))

    def test_absent_content_type_remains_empty_for_content_sniffing(self):
        data, _ = self.fetch_mock(_Response(b"<!doctype html><p>Text</p>", headers={}))
        self.assertEqual(data["content_type"], "")
        self.assertIsNone(data["charset"])

    def test_rejects_non_http_credentials_control_characters_and_bad_ports(self):
        for url in ("file:///etc/passwd", "data:text/html,x", "javascript:1", "https://a:b@example.org/",
                    "https://example.org/\nabc", "https://example.org:99999/", "https://", "https://bad host/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                extract_web.fetch_url(url)

    def test_private_local_host_is_allowed_and_unicode_url_normalized(self):
        self.assertEqual(extract_web._http_url("http://127.0.0.1:8080/"), "http://127.0.0.1:8080/")
        self.assertEqual(extract_web._http_url("https://例子.test/正文"), "https://xn--fsqu00a.test/%E6%AD%A3%E6%96%87")

    def test_redirect_handler_validates_every_new_destination(self):
        handler = extract_web._SafeRedirects()
        req = Request("https://example.org/start")
        for target in ("file:///tmp/page", "https://user:pass@example.org/end", "https://example.org/\nend"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(req, None, 302, "Found", {}, target)
        redirected = handler.redirect_request(req, None, 302, "Found", {}, "https://example.org/end")
        self.assertEqual(redirected.full_url, "https://example.org/end")
        self.assertEqual(handler.max_redirections, 6)

    def test_redirect_body_is_closed_without_unbounded_read(self):
        handler = extract_web._SafeRedirects(deadline=25)
        handler.parent = Mock()
        req = Request("https://example.org/start")
        response = Mock()
        with patch.object(extract_web.time, "monotonic", return_value=10):
            handler.http_error_302(req, response, 302, "Found", {"Location": "/next"})
        response.read.assert_not_called()
        response.close.assert_called_once()
        self.assertEqual(handler.parent.open.call_args.kwargs["timeout"], 15)
        self.assertEqual(handler.parent.open.call_args.args[0].full_url, "https://example.org/next")

    def test_redirect_limit_and_invalid_location_are_enforced_before_open(self):
        handler = extract_web._SafeRedirects()
        handler.parent = Mock()
        req = Request("https://example.org/start")
        req.timeout = 20
        req._adhd_redirect_count = 6
        for location in ("https://example.org/end", "file:///private/page", "/\r\nwrong"):
            response = Mock()
            with self.subTest(location=location), self.assertRaises(ValueError):
                handler.http_error_302(req, response, 302, "Found", {"Location": location})
            response.close.assert_called_once()
        handler.parent.open.assert_not_called()

    def test_large_declared_body_rejected_before_reading(self):
        response = _Response(headers={"Content-Length": str(extract_web.MAX_DOWNLOAD_BYTES + 1)})
        with self.assertRaisesRegex(ValueError, "20 MiB"):
            self.fetch_mock(response)

    def test_large_undeclared_body_rejected_while_reading(self):
        with patch.object(extract_web, "MAX_DOWNLOAD_BYTES", 20), self.assertRaisesRegex(ValueError, "20 MiB"):
            self.fetch_mock(_Response(b"x" * 21))

    def test_exact_size_allowed(self):
        with patch.object(extract_web, "MAX_DOWNLOAD_BYTES", 20):
            data, _ = self.fetch_mock(_Response(b"x" * 20))
        self.assertEqual(len(data["body"]), 20)

    def test_truncated_download_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "不完整"):
            self.fetch_mock(_Response(b"partial", headers={"Content-Length": "50"}))

    def test_download_deadline_and_socket_timeouts_actionable(self):
        with patch.object(extract_web.time, "monotonic", side_effect=[0, 0, 21]), self.assertRaisesRegex(ValueError, "超时"):
            self.fetch_mock(_Response())
        for error in (socket.timeout(), URLError(socket.timeout()), HTTPError("https://example.org", 403, "Forbidden", {}, None)):
            opener = Mock()
            opener.open.side_effect = error
            with self.subTest(error=error), patch.object(extract_web, "build_opener", return_value=opener), self.assertRaises(ValueError):
                extract_web.fetch_url("https://example.org")

    def test_invalid_timeouts_and_compressed_response_rejected(self):
        for timeout in (0, -1, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                extract_web.fetch_url("https://example.org", timeout=timeout)
        with self.assertRaisesRegex(ValueError, "未压缩"):
            self.fetch_mock(_Response(headers={"Content-Encoding": "gzip"}))


if __name__ == "__main__":
    unittest.main()
