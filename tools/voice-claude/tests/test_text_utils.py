import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from text_utils import clean_for_tts, extract_answer, is_wake_word, normalize  # noqa: E402


class WakeWordTest(unittest.TestCase):
    def wake(self, text, loose=False):
        return is_wake_word(text, config.WAKE_PATTERNS, config.LOOSE_PATTERNS, loose)

    def test_variants(self):
        for t in ["ねぇ、クロード", "ねえ クロード", "ねー クロード", "ネエ くろーど", "ねぇクロードさん"]:
            self.assertTrue(self.wake(t), t)

    def test_not_wake(self):
        for t in ["", "クラウドに保存", "今日は いい 天気", "クロード"]:
            self.assertFalse(self.wake(t), t)

    def test_loose(self):
        self.assertTrue(self.wake("クロード", loose=True))

    def test_normalize(self):
        self.assertEqual(normalize("ねぇ、ｸﾛｰﾄﾞ！"), "ネエクロド")


class ExtractTest(unittest.TestCase):
    def test_answer_after_last_question(self):
        screen = "\n".join([
            "前の質問", "前の答え",
            "今日の天気は？", "晴れの予報です。", "傘は不要です。",
            "Copy", "Retry",
            "Claude can make mistakes. Please double-check responses.",
        ])
        self.assertEqual(extract_answer(screen, "今日の天気は", config.UI_NOISE_LINES),
                         "晴れの予報です。\n傘は不要です。")

    def test_same_question_twice_uses_last(self):
        screen = "天気は\n古い答え\n天気は\n新しい答え"
        self.assertEqual(extract_answer(screen, "天気は"), "新しい答え")

    def test_question_not_found(self):
        self.assertEqual(extract_answer("関係ない文字", "天気は"), "")


class CleanTest(unittest.TestCase):
    def test_markdown(self):
        out = clean_for_tts("## 見出し\n- **太字** と `code`\n```py\nprint(1)\n```\nhttps://example.com")
        self.assertNotIn("#", out)
        self.assertNotIn("*", out)
        self.assertNotIn("print", out)
        self.assertIn("太字", out)
        self.assertIn("（リンク）", out)

    def test_truncate(self):
        self.assertTrue(clean_for_tts("あ" * 50, 10).endswith("確認してください。"))


if __name__ == "__main__":
    unittest.main()
