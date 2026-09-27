#!/usr/bin/env python3
"""Show the reading layers of an explanation and flag parts that fail on their own.

Layers: headings, blocks («Коротко» and the others), the summary, bold phrases,
the first sentence of each section. Headings, «Коротко» and «Підсумок» should retell
the scenario alone; bold phrases and section openings should read without context.
Also checks the size of the main text and the «тож…» moral repeated at paragraph ends.
Whether a first-time reader understands the text is checked by a cold reader, not here.
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
WORD_LIMIT = 1000
# A closing moral that restates the paragraph; a few are fine, one per paragraph is a habit.
MORALS = {"тож", "отже", "так"}
MORAL_LIMIT = 2
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

        print("\n## Вступ і обсяг")
        intro = re.split(r"^> \*\*Коротко\*\*|^```|^## ", body, maxsplit=1, flags=re.M)[0]
        intro_paragraphs = list(paragraphs(intro))
        if len(intro_paragraphs) > 1:
            print(f"  ! вступ — {len(intro_paragraphs)} абзаци: сцена — один абзац, суть — у блоці «Коротко»")
            problems += 1
        opening = next(iter(paragraphs(body)), "")
        if STAMP.match(opening):
            print("  ! вступ починається з дати чи часу: почни з мети, проблеми чи дії")
            problems += 1
        prose = re.sub(r"^```.*?^```", "", body, flags=re.M | re.S)
        words = len(re.findall(r"[\w'’]+", prose))
        print(f"- основний текст: {words} слів")
        if words > WORD_LIMIT:
            print(f"  ! більше за {WORD_LIMIT}: обери менше речей або розділи на два пояснення")
            problems += 1
        codes = sorted(set(re.findall(r"`([^`\n]+)`", prose)))
        print(f"- позначень у `коді`: {len(codes)} — {', '.join(codes)}")
        print("  кожне, якого читач не бачив, має з'явитися після прикладу або зникнути")
        morals = [p for p in paragraphs(body) if first_word(sentences(p)[-1]) in MORALS and len(sentences(p)) > 1]
        if len(morals) > MORAL_LIMIT:
            print(f"  ! {len(morals)} абзаців закінчуються мораллю «тож/отже»: закінчуй новим фактом або дією")
            problems += 1

        print("\n## Перше речення розділу")
        for heading, section in zip(re.findall(r"^## (.+)$", body, flags=re.M), re.split(r"^## .+$", body, flags=re.M)[1:]):
            first = next(iter(paragraphs(section)), "")
            if not first or heading.startswith(("Чого ", "Підсумок")):
                continue
            opening_sentence = sentences(first)[0]
            print(f"- {heading} → {opening_sentence}")
            if first_word(opening_sentence) in BACK_REFERENCES:
                print(f"  ! перше речення розділу починається з відсилання назад: «{first_word(opening_sentence)}»")
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
    print(f"Зауважень: {problems}. Скрипт перевіряє форму; чи зрозумілий текст новій людині, перевіряє холодний читач.")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: layers.py <explanation.md> [...]")
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
