"""Examples of the word-counting behavior promised in CHANGE.md."""

import unittest

from counter import count_words


class WordCounterTests(unittest.TestCase):
    def test_empty_text_has_no_words(self):
        self.assertEqual(count_words(""), 0)

    def test_one_word(self):
        self.assertEqual(count_words("Hello"), 1)

    def test_words_separated_by_single_spaces(self):
        self.assertEqual(count_words("Small steps make progress"), 4)

    def test_repeated_spaces_do_not_add_words(self):
        self.assertEqual(count_words("Small  steps   make progress"), 4)

    def test_tabs_and_newlines_separate_words(self):
        self.assertEqual(count_words("Small\tsteps\nmake\r\nprogress"), 4)

    def test_surrounding_whitespace_does_not_add_words(self):
        self.assertEqual(count_words("  Small steps  "), 2)

    def test_punctuation_stays_inside_whitespace_delimited_words(self):
        self.assertEqual(count_words("Well-made tools, small wins!"), 4)


if __name__ == "__main__":
    unittest.main()
