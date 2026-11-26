"""Tests for scripts/check_prompts.py."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_prompts as chk  # noqa: E402

GOOD = """---
id: sample-prompt
title: A sample prompt
kind: video-generation
model: MiniMax H3
settings:
  aspect_ratio: "9:16"
account: social-dots
posts:
  - platform: youtube
    status: posted
    at: "2026-11-25T00:01:50Z"
    url: https://www.youtube.com/shorts/abc
date: 2026-11-24
adapted_from: null
result:
  type: video
  url: https://example.com/clip.mp4
  poster: null
  gallery: []
offer: free-growth-check-up
product: null
related: []
blanks: [landmark]
---

```text
Aerial video of {{landmark: the CN Tower}} at sunset.
```
"""


class PromptTests(unittest.TestCase):
    def check(self, text, name="sample-prompt", known=("sample-prompt",)):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{name}.md"
            path.write_text(text, encoding="utf-8")
            return chk.check_prompt(path, set(known))

    def test_good_prompt_passes(self):
        self.assertEqual(self.check(GOOD), [])

    def test_id_must_match_file_name(self):
        self.assertTrue(any("file name" in e for e in self.check(GOOD, name="other")))

    def test_missing_field(self):
        errors = self.check(GOOD.replace("offer: free-growth-check-up\n", ""))
        self.assertTrue(any("missing fields: offer" in e for e in errors))

    def test_unknown_kind(self):
        self.assertTrue(any("kind" in e for e in self.check(GOOD.replace("video-generation", "audio"))))

    def test_blanks_must_match_body(self):
        errors = self.check(GOOD.replace("blanks: [landmark]", "blanks: [city]"))
        self.assertTrue(any("blanks" in e for e in errors))

    def test_related_must_exist(self):
        errors = self.check(GOOD.replace("related: []", "related: [ghost]"))
        self.assertTrue(any("ghost" in e for e in errors))

    def test_posted_post_needs_url(self):
        errors = self.check(GOOD.replace("    url: https://www.youtube.com/shorts/abc\n", ""))
        self.assertTrue(any("required once a post is posted" in e for e in errors))

    def test_result_url_must_be_https(self):
        errors = self.check(GOOD.replace("https://example.com/clip.mp4", "http://example.com/clip.mp4"))
        self.assertTrue(any("result.url" in e for e in errors))

    def test_result_may_be_null(self):
        start = GOOD.index("result:")
        end = GOOD.index("offer:")
        self.assertEqual(self.check(GOOD[:start] + "result: null\n" + GOOD[end:]), [])

    def test_body_must_be_one_text_fence(self):
        errors = self.check(GOOD.replace("```text\n", "").replace("\n```", ""))
        self.assertTrue(any("fenced block" in e for e in errors))

    def test_no_frontmatter(self):
        self.assertTrue(self.check("just text\n"))


class MediaTests(unittest.TestCase):
    def test_large_media_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clip.mp4").write_bytes(b"0" * (chk.MAX_MEDIA_BYTES + 1))
            (root / "small.png").write_bytes(b"0" * 10)
            self.assertEqual(chk.committed_media(root), ["clip.mp4"])


class RepositoryTests(unittest.TestCase):
    def test_repository_prompts_pass(self):
        self.assertEqual(chk.main(), 0)


if __name__ == "__main__":
    unittest.main()
