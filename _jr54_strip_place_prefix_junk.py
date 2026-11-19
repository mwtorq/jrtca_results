"""Strip leading OCR junk before place ordinals on 1990-2001 HQ files."""
from __future__ import annotations

from pathlib import Path
import re
import sys

sys.path.insert(0, ".")
import yearbook_ocr as yo

ROOT = Path("Updated Yearbook Scans")


def count_gaps(lines: list[str]) -> int:
    place_ranks: list[tuple[int, str]] = []
    n = 0

    def flush() -> None:
        nonlocal place_ranks, n
        if len(place_ranks) >= 2:
            for (a, _), (b, _) in zip(place_ranks, place_ranks[1:]):
                if b > a + 1:
                    n += 1
        place_ranks = []

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if (
            yo._PAGE_BREAK_RE.match(s)
            or yo._COLUMN_MARK_RE.match(s)
            or yo._MARKER_RE.match(s)
        ):
            continue
        if yo._is_hq_metadata_line(s):
            continue
        if yo._is_non_place_result_line(s) or yo._BEST_RESERVE_SECTION_RE.match(s):
            flush()
            continue
        if re.match(
            r"(?i)^(?:Conformation|Racing|Go-?to-?Ground|Agility|Obedience|Working(?:\s+Terrier)?)\s+DIVISION\b",
            s,
        ):
            flush()
            continue
        m = re.match(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:", s)
        if m:
            rank = int(m.group(1))
            if 1 <= rank <= 12:
                if place_ranks and rank <= place_ranks[-1][0]:
                    flush()
                place_ranks.append((rank, s))
                continue
        if yo._looks_like_class_header_line(s) or yo._SECTIONISH_RE.search(s):
            flush()
            continue
    flush()
    return n


def clean_text(text: str) -> tuple[str, int]:
    new_lines = []
    changed = 0
    for line in text.splitlines():
        m = re.search(r"(?i)(\d+(?:st|nd|rd|th)\s*:)", line)
        if m and not re.match(r"(?i)^\d+(?:st|nd|rd|th)\s*:", line.strip()):
            prefix = line[: m.start()]
            ps = prefix.strip()
            # Pure punct/space junk, or short OCR crumbs (e.g. "r", "aa", "ap") before place
            if len(ps) <= 25 and (
                re.fullmatch(r"[\s\W_]*", prefix or " ")
                or re.fullmatch(r"[\W_\s]*[A-Za-z]{1,4}[\W_\s]*", prefix)
            ):
                nl = line[m.start() :]
                if nl != line:
                    changed += 1
                    line = nl
        new_lines.append(line)
    new = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    return new, changed


def year_of(p: Path) -> int | None:
    for part in p.parts:
        if len(part) >= 4 and part[:4].isdigit() and "1990" <= part[:4] <= "2001":
            return int(part[:4])
    return None


def main() -> None:
    rows = []
    total_before = total_after = total_changed = 0
    for p in sorted(ROOT.rglob("*_ocr_hqmax.txt")):
        if year_of(p) is None:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        before = count_gaps(text.splitlines())
        new, changed = clean_text(text)
        after = count_gaps(new.splitlines())
        if changed and new != text:
            p.write_text(new, encoding="utf-8")
        total_before += before
        total_after += after
        total_changed += changed
        if before != after or changed:
            rows.append((before - after, before, after, changed, str(p)))
    rows.sort(reverse=True)
    print(f"TOTAL gaps {total_before} -> {total_after} (cleaned lines {total_changed})")
    for delta, b, a, c, path in rows[:30]:
        print(f"  {b:4d}->{a:4d} (Δ{delta:3d}) cleaned={c:4d} | {path}")


if __name__ == "__main__":
    main()
