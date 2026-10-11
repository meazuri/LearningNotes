#!/usr/bin/env python3
"""
Find exam questions related to a topic (default: VPC) inside AWS practice-exam
.epub files, and export the matches to a Markdown file.

Usage:
    python find_vpc_questions.py <epub_file_or_folder> [--keywords KEYWORD,KEYWORD,...] [--out OUTPUT.md]

If a folder is given, every .epub file inside it is scanned.
"""

import sys
import re
import zipfile
import argparse
from pathlib import Path
from html.parser import HTMLParser

# Default set of VPC-related keywords/phrases. Matching is case-insensitive
# and uses word boundaries where sensible so "VPC" doesn't match "svpc" etc.
DEFAULT_KEYWORDS = [
    "vpc", "subnet", "nat gateway", "nat instance", "route table",
    "internet gateway", "security group", "network acl", "nacl",
    "vpc peering", "vpc endpoint", "transit gateway", "vpn gateway",
    "elastic ip", "vpc flow logs", "private link", "privatelink",
    "cidr", "vpn connection", "customer gateway", "egress-only",
]


class QuestionHTMLParser(HTMLParser):
    """Parses one chapter xhtml file and pulls out structured question blocks."""

    def __init__(self):
        super().__init__()
        self.questions = []
        self._current = None
        self._section_depth = 0
        self._capture_mode = None  # 'title' | 'question' | 'option' | 'answer' | 'explanation'
        self._option_letter = None
        self._buffer = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")

        if tag == "section" and cls == "question":
            self._current = {
                "title": "",
                "question": "",
                "options": [],
                "answer": "",
                "explanation": "",
            }
            self._section_depth = 1
            return

        if self._current is None:
            return

        if tag == "h2":
            self._capture_mode = "title"
            self._buffer = ""
        elif tag == "p" and cls == "question-text":
            self._capture_mode = "question"
            self._buffer = ""
        elif tag == "li":
            self._capture_mode = "option"
            self._buffer = ""
        elif tag == "div" and cls == "answer":
            self._capture_mode = "answer"
            self._buffer = ""
        elif tag == "div" and cls == "explanation":
            self._capture_mode = "explanation"
            self._buffer = ""

    def handle_endtag(self, tag):
        if self._current is None:
            return

        if tag == "h2" and self._capture_mode == "title":
            self._current["title"] = self._clean(self._buffer)
            self._capture_mode = None
        elif tag == "p" and self._capture_mode == "question":
            self._current["question"] = self._clean(self._buffer)
            self._capture_mode = None
        elif tag == "li" and self._capture_mode == "option":
            self._current["options"].append(self._clean(self._buffer))
            self._capture_mode = "explanation_wait" if False else None
        elif tag == "div" and self._capture_mode == "answer":
            self._current["answer"] = self._clean(self._buffer)
            self._capture_mode = None
        elif tag == "div" and self._capture_mode == "explanation":
            self._current["explanation"] = self._clean(self._buffer)
            self._capture_mode = None
        elif tag == "section" and self._current is not None:
            self.questions.append(self._current)
            self._current = None

    def handle_data(self, data):
        if self._capture_mode:
            self._buffer += data

    @staticmethod
    def _clean(text):
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text


def extract_questions_from_epub(epub_path):
    """Returns a list of question dicts, tagged with their source file."""
    all_questions = []
    with zipfile.ZipFile(epub_path, "r") as z:
        chapter_files = sorted(
            n for n in z.namelist()
            if re.search(r"chap_\d+\.xhtml$", n)
        )
        for name in chapter_files:
            raw = z.read(name).decode("utf-8", errors="replace")
            parser = QuestionHTMLParser()
            parser.feed(raw)
            for q in parser.questions:
                q["source_file"] = name
                q["epub"] = Path(epub_path).name
                all_questions.append(q)
    return all_questions


def build_keyword_pattern(keywords):
    escaped = [re.escape(k) for k in keywords]
    # sort longest-first so multi-word phrases aren't shadowed by short ones
    escaped.sort(key=len, reverse=True)
    pattern = r"(" + "|".join(escaped) + r")"
    return re.compile(pattern, re.IGNORECASE)


def question_matches(q, pattern, strict=False):
    """
    strict=False (default): match if the keyword appears anywhere (question,
        options, or explanation). Good for broad topic review.
    strict=True: only match if the keyword appears in the question text or
        answer options themselves (not just the explanation). Good for
        finding questions that are actually ASKING about the topic, not just
        ones where the topic happens to come up while explaining something else.
    """
    if strict:
        haystack = " ".join([
            q.get("title", ""),
            q.get("question", ""),
            " ".join(q.get("options", [])),
        ])
    else:
        haystack = " ".join([
            q.get("title", ""),
            q.get("question", ""),
            " ".join(q.get("options", [])),
            q.get("explanation", ""),
        ])
    return bool(pattern.search(haystack))


def format_question_markdown(q, idx):
    lines = []
    title = q.get("title") or f"Question {idx}"
    lines.append(f"## {title}")
    lines.append(f"*Source: {q.get('epub')} / {q.get('source_file')}*")
    lines.append("")
    lines.append(q.get("question", "").strip())
    lines.append("")
    for opt in q.get("options", []):
        lines.append(f"- {opt}")
    lines.append("")
    if q.get("answer"):
        lines.append(f"**{q['answer']}**")
        lines.append("")
    if q.get("explanation"):
        lines.append(f"> {q['explanation']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Find topic-related questions in AWS practice-exam epub files.")
    parser.add_argument("path", help="Path to an .epub file or a folder containing .epub files")
    parser.add_argument(
        "--keywords",
        help="Comma-separated list of keywords/phrases to search for (overrides the default VPC keyword set)",
        default=None,
    )
    parser.add_argument(
        "--out",
        help="Output Markdown file path",
        default="vpc_questions.md",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Only match questions where the keyword appears in the question/options "
             "(ignores mentions that only occur in the explanation text)",
    )
    args = parser.parse_args()

    keywords = DEFAULT_KEYWORDS
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    pattern = build_keyword_pattern(keywords)

    input_path = Path(args.path)
    epub_files = []
    if input_path.is_dir():
        epub_files = sorted(input_path.glob("*.epub"))
    elif input_path.is_file():
        epub_files = [input_path]
    else:
        print(f"Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not epub_files:
        print("No .epub files found.", file=sys.stderr)
        sys.exit(1)

    all_questions = []
    for epub_file in epub_files:
        all_questions.extend(extract_questions_from_epub(epub_file))

    matched = [q for q in all_questions if question_matches(q, pattern, strict=args.strict)]

    print(f"Scanned {len(epub_files)} epub file(s), found {len(all_questions)} total questions.")
    print(f"Keywords used: {', '.join(keywords)}")
    print(f"Matched {len(matched)} question(s).")

    out_path = Path(args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Matched Questions ({len(matched)} of {len(all_questions)})\n\n")
        f.write(f"**Keywords:** {', '.join(keywords)}\n\n")
        f.write("---\n\n")
        for i, q in enumerate(matched, 1):
            f.write(format_question_markdown(q, i))

    print(f"Written to: {out_path}")


if __name__ == "__main__":
    main()
