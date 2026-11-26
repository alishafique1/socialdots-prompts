"""Tests for scripts/check_privacy.py.

Every sample of private material is assembled at run time from pieces, so
this file never contains a real-looking secret, address or path itself.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_privacy as cp  # noqa: E402


def rules_hit(text, denylist=(), allowlist=()):
    findings = cp.scan_text("x.md", text, list(denylist), {a.lower() for a in allowlist})
    return sorted({f.rule for f in findings})


class RuleTests(unittest.TestCase):
    def test_clean_prompt_passes(self):
        text = (
            "Vertical 9:16 photorealistic aerial video of the CN Tower at sunset.\n"
            "[0s] Empty lot. [2s] Cyan pillars rise. Seed 42, 576x1024, 362 frames.\n"
            "See https://www.youtube.com/shorts/WDajKrJZylQ and "
            "https://www.tiktok.com/@socialdots.ca/video/7711894554726698261\n"
        )
        self.assertEqual(rules_hit(text), [])

    def test_api_keys_and_tokens(self):
        samples = [
            "sk-" + "ant-" + "a" * 30,
            "gh" + "p_" + "A1b2" * 9,
            "github" + "_pat_" + "x" * 30,
            "AK" + "IA" + "ABCDEFGHIJKLMNOP",
            "xo" + "xb-" + "1234567890-abc",
            "pi" + "t-" + "0123abcd-0123-4567-89ab-0123456789ab",
            "ey" + "J" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12,
            "Bear" + "er " + "q" * 24,
            "api" + "_key: " + "Z" * 20,
            "-----BEGIN RSA " + "PRIVATE KEY-----",
        ]
        for sample in samples:
            with self.subTest(sample=sample[:8]):
                self.assertTrue(rules_hit(sample), sample[:8])

    def test_email(self):
        self.assertEqual(rules_hit("write to " + "someone" + "@" + "example.ca"), ["email"])

    def test_phone_numbers(self):
        for sample in ["(416) 555-" + "0199", "416-555-" + "0199", "+1 416 555 " + "0199", "+1416555" + "0199"]:
            with self.subTest(sample=sample):
                self.assertEqual(rules_hit(sample), ["phone"])

    def test_internal_paths(self):
        samples = [
            "/Us" + "ers/someone/Code/factory",
            "~" + "/Social Dots Content/00-inbox",
            "/volu" + "me1/work/content-library",
            "." + "data/inputs/refs/ref-01.jpg",
            "2-" + "Areas/work/social-dots",
            "life" + "-os vault",
            "." + "env.secrets",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertEqual(rules_hit(sample), ["internal-path"])

    def test_higgsfield_element_ids(self):
        uuid = "3f2b8c1e" + "-4d5a-4b6c-9e7f-0a1b2c3d4e5f"
        self.assertEqual(rules_hit("use element " + uuid), ["higgsfield-element-id"])
        self.assertEqual(rules_hit("element" + "_id: abc123"), ["higgsfield-element-id"])

    def test_allowlisted_element_id_passes(self):
        uuid = "3f2b8c1e" + "-4d5a-4b6c-9e7f-0a1b2c3d4e5f"
        self.assertEqual(rules_hit("use element " + uuid, allowlist=[uuid.upper()]), [])

    def test_client_names_from_denylist(self):
        name = "Acme" + " Bakery"
        self.assertEqual(rules_hit("an ad for acme bakery", denylist=[name]), ["client-name"])
        self.assertEqual(rules_hit("an ad for acme bakeryland", denylist=[name]), [])

    def test_location_id(self):
        self.assertEqual(rules_hit("location" + "Id: " + "a1B2c3D4e5F6g7"), ["internal-id"])


class DenylistLoadingTests(unittest.TestCase):
    def test_env_and_file_are_merged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / cp.DENYLIST_FILE).write_text("# comment\nBeta Co\n", encoding="utf-8")
            terms = cp.load_denylist(root, {cp.DENYLIST_ENV: "Alpha Ltd, Gamma\nBeta Co"})
            self.assertEqual(terms, ["Alpha Ltd", "Beta Co", "Gamma"])


class MainTests(unittest.TestCase):
    def make_repo(self, files):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.addCleanup(tmp.cleanup)
        return root

    def test_require_denylist_fails_without_names(self):
        root = self.make_repo({"prompts/a.md": "clean"})
        self.assertEqual(cp.main(["--require-denylist"], root=root, env={}), 2)

    def test_clean_repo_passes(self):
        root = self.make_repo({"prompts/a.md": "clean", "README.md": "hello"})
        self.assertEqual(cp.main([], root=root, env={cp.DENYLIST_ENV: "Acme Bakery"}), 0)

    def test_finding_fails(self):
        root = self.make_repo({"prompts/a.md": "made for Acme Bakery"})
        self.assertEqual(cp.main([], root=root, env={cp.DENYLIST_ENV: "Acme Bakery"}), 1)

    def test_tests_directory_is_not_scanned(self):
        root = self.make_repo({"tests/t.py": "Acme Bakery"})
        self.assertEqual(cp.main([], root=root, env={cp.DENYLIST_ENV: "Acme Bakery"}), 0)


if __name__ == "__main__":
    unittest.main()
