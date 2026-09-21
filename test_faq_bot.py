#!/usr/bin/env python3
"""Проверки FAQ-бота: python3 -m unittest test_faq_bot.py -v"""

import unittest

import faq_bot


class FaqTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = faq_bot.load_faq()

    def matched_question(self, query):
        entry, _ = faq_bot.find_best(query, self.entries)
        return entry.question if entry else None

    def test_five_entries_loaded(self):
        self.assertEqual(len(self.entries), 5)
        for entry in self.entries:
            self.assertTrue(entry.question)
            self.assertTrue(entry.answer)

    def test_paraphrased_questions_hit_right_entry(self):
        cases = {
            "во сколько начало?": "Когда",
            "а можно одному, без команды?": "Какого размера",
            "какие треки есть": "Какие есть треки",
            "куда сдавать проект": "Куда и в каком виде",
            "что дают победителям": "Какие призы",
        }
        for query, expected_prefix in cases.items():
            with self.subTest(query=query):
                matched = self.matched_question(query)
                self.assertIsNotNone(matched, "бот не нашёл ответ на %r" % query)
                self.assertTrue(
                    matched.startswith(expected_prefix),
                    "%r -> %r" % (query, matched),
                )

    def test_offtopic_questions_return_none(self):
        for query in ("какая завтра погода", "как дела с ипотекой", "расскажи анекдот"):
            with self.subTest(query=query):
                self.assertIsNone(faq_bot.answer(query, self.entries))

    def test_normalize_strips_case_and_endings(self):
        self.assertEqual(faq_bot.normalize("Командой!"), faq_bot.normalize("команды"))
        self.assertEqual(faq_bot.normalize("а и в на"), [])


if __name__ == "__main__":
    unittest.main()
