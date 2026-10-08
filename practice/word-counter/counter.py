"""Count whitespace-delimited words in text supplied on the command line."""

import argparse


def count_words(text):
    """Treat runs of whitespace as separators; keep punctuation in each word."""
    return len(text.split())


def main():
    parser = argparse.ArgumentParser(
        description="Count words separated by whitespace. Put your text in quotes."
    )
    parser.add_argument("text", help='Text to count, for example "Small steps make progress"')
    args = parser.parse_args()
    print(f"Words: {count_words(args.text)}")


if __name__ == "__main__":
    main()
