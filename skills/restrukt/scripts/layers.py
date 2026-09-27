#!/usr/bin/env python3
"""Show the reading layers of an explanation and flag parts that fail on their own.

Layers: headings; bold phrases; first and last sentence of each paragraph.
Each layer should retell the scenario without the rest of the text.
"""

import re
import sys
from pathlib import Path

APPENDIX = re.compile(r"^## Додаток", flags=re.M)
# Words that point back to something the isolated phrase does not contain.
BACK_REFERENCES = {
    "її", "його", "їх", "їй", "йому", "їм", "це", "цього", "цьому", "цим",
    "він", "вона", "воно", "вони", "там", "тут", "той", "те", "ті",
    "тому", "отже", "тож", "також", "звідси",
    "it", "this", "that", "they", "them", "so", "therefore",
}
TITLE_WORDS = 12
# Block labels and how many of each a text may hold (0 — as needed).
BLOCK_LIMITS = {"Коротко": 1, "Визначення": 0, "Увага": 3, "Порада": 3, "Як гадаєш?": 2}
# A calendar or clock stamp as the opening words is decoration, not a reason to read.
STAMP = re.compile(
    r"^(понеділ|вівтор|серед|четвер|п['’]ятниц|субот|неділ|ранок|вечір|ніч|опівдні|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|evening|\d{1,2}[:.]\d{2})",
    flags=re.I,
)


def body_of(text: str) -> str:
    match = APPENDIX.search(text)
    return text[: match.start()] if match else text


def paragraphs(body: str):
    body = re.sub(r"^```.*?^```", "", body, flags=re.M | re.S)
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block or block.startswith(("#", "|", "-", ">", "---")) or block[0].isdigit():
            continue
        if block.startswith("*") and not block.startswith("**"):
            continue  # italic caption under a diagram
        yield " ".join(block.split()).replace("**", "")


def sentences(paragraph: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+(?=[\"«*`(]?[A-ZА-ЯІЇЄҐ0-9])", paragraph)
    return [part for part in parts if part]


def first_word(phrase: str) -> str:
    words = re.findall(r"[\w'’]+", phrase.lower())
    return words[0] if words else ""


def main(paths: list[str]) -> int:
    problems = 0
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        body = body_of(text)
        print(f"# {path}\n")

        print("## Заголовки")
        headings = re.findall(r"^#{1,3} (.+)$", body, flags=re.M)
        for heading in headings:
            print(f"- {heading}")
        title = re.search(r"^# (.+)$", body, flags=re.M)
        if title and len(title[1].split()) > TITLE_WORDS:
            print(f"  ! заголовок довший за {TITLE_WORDS} слів: подробиці — у вступ")
            problems += 1

        print("\n## Блоки")
        blocks = re.findall(r"^> \*\*(.+?)\*\*\s*·?\s*(.*)$", body, flags=re.M)
        counts: dict[str, int] = {}
        for label, rest in blocks:
            print(f"- {label} · {rest}")
            counts[label] = counts.get(label, 0) + 1
            if label not in BLOCK_LIMITS:
                print(f"  ! невідома мітка «{label}»: лише {', '.join(BLOCK_LIMITS)}")
                problems += 1
        for label, limit in BLOCK_LIMITS.items():
            if limit and counts.get(label, 0) > limit:
                print(f"  ! «{label}» — {counts[label]}, більше за {limit}")
                problems += 1
        if not counts.get("Коротко"):
            print("  ! немає блоку «Коротко» після вступу")
            problems += 1
        if not re.search(r"^## Підсумок", body, flags=re.M):
            print("  ! немає розділу «Підсумок»")
            problems += 1

        print("\n## Жирне")
        bold = re.findall(r"\*\*(.+?)\*\*", body)
        for phrase in bold:
            print(f"- {phrase}")
            if first_word(phrase) in BACK_REFERENCES:
                print(f"  ! жирне починається з відсилання назад: «{first_word(phrase)}»")
                problems += 1

        print("\n## Перше й останнє речення")
        intro = re.split(r"^> \*\*Коротко\*\*|^```|^## ", body, maxsplit=1, flags=re.M)[0]
        intro_paragraphs = list(paragraphs(intro))
        if len(intro_paragraphs) > 1:
            print(f"  ! вступ — {len(intro_paragraphs)} абзаци: сцена — один абзац, суть — у блоці «Коротко»")
            problems += 1
        opening = next(iter(paragraphs(body)), "")
        if STAMP.match(opening):
            print("  ! вступ починається з дати чи часу: почни з мети, проблеми чи дії")
            problems += 1
        for paragraph in paragraphs(body):
            parts = sentences(paragraph)
            print(f"- {parts[0]}")
            if len(parts) > 1:
                print(f"  … {parts[-1]}")
            if first_word(parts[0]) in BACK_REFERENCES:
                print(f"  ! перше речення починається з відсилання назад: «{first_word(parts[0])}»")
                problems += 1

        sections = re.split(r"^## .+$", body, flags=re.M)[1:]
        for heading, section in zip(re.findall(r"^## (.+)$", body, flags=re.M), sections):
            if heading.startswith(("Чого ", "Підсумок")):
                continue  # open questions: «### Q1 · …» and a paragraph, no bold
            if "**" not in section and list(paragraphs(section)):
                print(f"! розділ без жирного: «{heading}»")
                problems += 1
        if re.search(r"\bкористувач\w*\b", body, flags=re.I) and "ти" not in body.lower().split():
            print("! головний герой — «користувач», а не «ти»")
            problems += 1
        if not APPENDIX.search(text):
            print("! немає додатка «Звідки це відомо»")
            problems += 1
        print()
    print(f"Зауважень: {problems}. Прочитай кожен шар як окремий текст: скрипт не оцінює зміст.")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: layers.py <explanation.md> [...]")
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
