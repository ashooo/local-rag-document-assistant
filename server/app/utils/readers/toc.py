import re
from difflib import SequenceMatcher

TOC_KEYWORDS = [
    "table of contents",
    "contents",
    "toc",
    "list of tables",
    "list of figures",
    "list of appendices",
    "list of abbreviations",
    "talaan ng nilalaman",
    "nilalaman",
]

TOC_LINE_PATTERNS = [
    # Introduction ........ 1
    r"^(?P<title>.+?)\.{2,}\s*(?P<page>[ivxlcdmIVXLCDM]+|\d+)$",

    # 1. Introduction ........ 1
    # 1.1 Background ........ 3
    r"^(?P<number>\d+(\.\d+)*)\.?\s+(?P<title>.+?)\.{2,}\s*(?P<page>[ivxlcdmIVXLCDM]+|\d+)$",

    # Chapter 1 Introduction ........ 1
    r"^(?P<title>(chapter|section)\s+[\divxlcdmIVXLCDM]+.*?)(\.{2,}|\s{2,})\s*(?P<page>[ivxlcdmIVXLCDM]+|\d+)$",

    # I. Introduction ........ 1
    # II. Methodology ........ 20
    r"^(?P<number>[IVXLCDM]+)\.?\s+(?P<title>.+?)\.{2,}\s*(?P<page>[ivxlcdmIVXLCDM]+|\d+)$",

    # Introduction 1
    r"^(?P<title>[A-Za-z][A-Za-z0-9\s,\-:()\/&]{2,80})\s+(?P<page>[ivxlcdmIVXLCDM]+|\d+)$",

    # 1 Introduction 1
    # 1.1 Background 3
    r"^(?P<number>\d+(\.\d+)*)\.?\s+(?P<title>[A-Za-z][A-Za-z0-9\s,\-:()\/&]{2,80})\s+(?P<page>[ivxlcdmIVXLCDM]+|\d+)$",
]


def get_toc_candidate_text(
    pages: list[dict],
    max_pages: int = 10,
    max_chars: int = 12000,
) -> str:
    if not pages:
        return ""

    selected_pages = pages[:max_pages]
    text = "\n".join(page.get("text", "") for page in selected_pages)

    return text[:max_chars]


def match_toc(text: str, threshold: float = 0.8) -> str | None:
    words = text.split()

    if not words:
        return None

    max_len = max(len(keyword.split()) for keyword in TOC_KEYWORDS)

    best_score = 0.0
    best_phrase = None

    for n in range(1, max_len + 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])

            for keyword in TOC_KEYWORDS:
                score = SequenceMatcher(
                    None,
                    keyword.lower(),
                    phrase.lower()
                ).ratio()

                if score > best_score and score >= threshold:
                    best_score = score
                    best_phrase = phrase

    if not best_phrase:
        return None

    index = text.lower().find(best_phrase.lower())

    if index == -1:
        return None

    return text[index + len(best_phrase):].lstrip(" \t\n:-.")


def clean_toc_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"\.{2,}", "", title)
    title = re.sub(r"\s+", " ", title)
    title = title.strip(" .:-")

    return title


def extract_toc_content(text: str | None) -> list[dict]:
    entries = []

    if not text:
        return entries

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        for pattern in TOC_LINE_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE)

            if not match:
                continue

            data = match.groupdict()

            title = data.get("title")
            page = data.get("page")
            number = data.get("number")

            if not title or not page:
                continue

            entries.append({
                "number": number.strip() if number else None,
                "title": clean_toc_title(title),
                "page": page.strip(),
                "raw_line": line,
            })

            break

    return entries


def extract_toc(pages: list[dict]) -> list[dict]:
    candidate_text = get_toc_candidate_text(pages)
    toc_text = match_toc(candidate_text)

    return extract_toc_content(toc_text)