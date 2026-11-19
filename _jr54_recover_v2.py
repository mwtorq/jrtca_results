"""JR-54 v2: evidence-gated place-gap recovery from PDF text layers.

Insert a missing place only when the PDF page that contains BOTH flanking
HQ neighbor dog names also shows that ordinal with a usable dog+owner body.
Never invent surnames. Unscannable gaps stay FAIL; notes go to sidecar only
(never inline between places — that falsely clears detectors).
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

import fitz

from yearbook_ocr import audit_results_ocr_page

BASE = Path("_ocr_baseline_v2/yearbook_1990_2001")
UPDATED = Path("Updated Yearbook Scans")
TARGET = {
    "place_rank_gap",
    "3rd_then_5th_no_4",
    "2nd_then_4th_no_3",
    "1st_then_3rd_no_2",
    "agility_racing_smash",
}
PAGE_RE = re.compile(r"(?i)^---\s*page\s+(\d+)")
PLACE_RE = re.compile(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:\s*(.+)$")


@dataclass
class Log:
    year: int
    file: str
    hq: str = ""
    pdf: str = ""
    before: int = 0
    after: int = 0
    recovered: list[str] = field(default_factory=list)
    glued: list[str] = field(default_factory=list)
    parked_sidecar: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def year_from_hq(hq: Path) -> int | None:
    for p in hq.parts:
        if p.isdigit() and len(p) == 4:
            return int(p)
    return None


def find_hq(year: int, file: str) -> Path | None:
    ydir = BASE / str(year)
    hits = list(ydir.rglob(file)) if ydir.exists() else []
    return hits[0] if hits else None


def find_pdf(year: int, hq: Path) -> Path | None:
    stem = hq.name.replace("_ocr_hqmax.txt", "")
    # meta source= path
    meta = hq.with_name(hq.name.replace("_ocr_hqmax.txt", "_ocr_hqmax.meta.txt"))
    if meta.exists():
        for ln in meta.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.lower().startswith("source="):
                sp = Path(ln.split("=", 1)[1].strip().strip('"'))
                if sp.exists():
                    return sp
                # try Updated mirror of same filename
                hits = [p for p in UPDATED.rglob(sp.name) if str(year) in p.as_posix()]
                if hits:
                    return hits[0]
                # Yearbook Scans (non-Updated)
                ys = Path("Yearbook Scans")
                if ys.exists():
                    hits = list(ys.rglob(sp.name))
                    if hits:
                        return hits[0]
    # Prefer Updated paths that include the year
    cands = []
    for p in UPDATED.rglob(stem + ".pdf"):
        if str(year) in p.parts or str(year) in p.as_posix():
            cands.append(p)
    if cands:
        return cands[0]
    if stem == "scan":
        for p in [
            UPDATED / str(year) / "scan.pdf",
            UPDATED / f"{year} Yearbook Vol 1" / "scan.pdf",
        ]:
            if p.exists():
                return p
        return None
    # Yearbook Scans fallback by stem
    ys = Path("Yearbook Scans")
    if ys.exists():
        hits = list(ys.rglob(stem + ".pdf"))
        if hits:
            return hits[0]
    hits = list(UPDATED.rglob(stem + ".pdf"))
    return hits[0] if hits else None


def find_updated_hq(year: int, hq: Path) -> Path | None:
    stem = hq.name
    cands = [p for p in UPDATED.rglob(stem) if str(year) in p.as_posix()]
    if cands:
        return cands[0]
    hits = list(UPDATED.rglob(stem))
    # avoid cross-year scan_ocr_hqmax
    if stem == "scan_ocr_hqmax.txt":
        for p in hits:
            if str(year) in p.as_posix():
                return p
        return None
    return hits[0] if hits else None


def ordinal(n: int) -> str:
    if n % 100 in (11, 12, 13):
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def dog_key(place_line: str) -> str:
    body = place_line.split(":", 1)[-1].strip()
    name = body.split(",")[0].strip()
    name = re.sub(r"\s+", " ", name)
    return name.lower()[:40]


def clean_body(body: str) -> str | None:
    body = re.sub(r"\s+", " ", body).strip()
    body = body.replace("&amp;", "&")
    if re.match(r"(?i)^\d+(?:st|nd|rd|th)\s*:", body):
        return None
    body = re.sub(r"(?i)\bown(?:ui|nl|ocl|u!|od|&l|<i)\b", "owned", body)
    body = re.sub(r"(?i)\bowned\s+by\b", "owned by", body)
    body = re.sub(r"(?i)\bowned\b(?!\s+by)", "owned by", body)
    if len(body) < 6:
        return None
    if not re.search(r"(?i)owned by|handled by", body):
        return None
    # require some letters in dog side
    dog = body.split(",")[0]
    if sum(ch.isalpha() for ch in dog) < 3:
        return None
    # reject heavy garbage ratio
    if sum(ch.isalpha() or ch.isspace() for ch in body) < len(body) * 0.55:
        return None
    # light OCR letter fixes only on known safe tokens already partially present
    body = body.replace("Farrrnlitf", "Farmcliff").replace("Farmdiff", "Farmcliff")
    body = body.replace("Farrrnltff", "Farmcliff").replace("Farnnltff", "Farmcliff")
    body = body.replace("Wynnewaod", "Wynnewood").replace("Foxfiold", "Foxfield")
    body = body.replace("Grinstoul", "Grinstead")
    body = re.sub(r"Yoneluna\$", "Yonelunas", body)
    body = re.sub(r"\s+[–—-]\s*Entries:.*$", "", body)
    return body.strip(" ,;")


def parse_pdf_places(page_text: str) -> list[tuple[int, str]]:
    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
    places: list[tuple[int, str]] = []
    ord_only = re.compile(r"(?i)^(?:(\d+)\s*(?:st|nd|rd|th)|[l1I]st)\s*:?\s*$")
    ord_inline = re.compile(r"(?i)^(?:(\d+)\s*(?:st|nd|rd|th)|[l1I]st)\s*:?\s*(.+)$")
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = ord_inline.match(ln)
        if m and m.group(2):
            rank = int(m.group(1) or 1)
            places.append((rank, m.group(2).strip()))
            i += 1
            continue
        m2 = ord_only.match(ln) or (
            re.match(r"(?i)^(\d+)\s*(?:st|nd|rd|th)\s*:?\s*$", ln)
        )
        if m2:
            rank = int(m2.group(1) or 1)
            body = lines[i + 1] if i + 1 < len(lines) else ""
            # skip if next is also ordinal
            if body and not re.match(r"(?i)^\d*(?:st|nd|rd|th)\s*:?\s*$", body) and not re.match(
                r"(?i)^[l1I]st\s*:?\s*$", body
            ):
                places.append((rank, body))
                i += 2
                continue
            i += 1
            continue
        i += 1
    return places


def find_gap_blocks(lines: list[str]) -> list[dict]:
    """Mirror place_rank_gap detector closely enough for recovery targets."""
    from yearbook_ocr import (
        _BEST_RESERVE_SECTION_RE,
        _COLUMN_MARK_RE,
        _MARKER_RE,
        _PAGE_BREAK_RE,
        _SECTIONISH_RE,
        _is_hq_metadata_line,
        _is_non_place_result_line,
        _looks_like_class_header_line,
    )

    gaps = []
    place_ranks: list[tuple[int, int, str]] = []
    header = ""

    def flush() -> None:
        nonlocal place_ranks
        if len(place_ranks) >= 2:
            for (a, ia, sa), (b, ib, sb) in zip(place_ranks, place_ranks[1:]):
                if b > a + 1:
                    gaps.append(
                        {
                            "header": header,
                            "a": a,
                            "b": b,
                            "ia": ia,
                            "ib": ib,
                            "sa": sa,
                            "sb": sb,
                            "missing": list(range(a + 1, b)),
                        }
                    )
        place_ranks = []

    for idx, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if _PAGE_BREAK_RE.match(s) or _COLUMN_MARK_RE.match(s) or _MARKER_RE.match(s):
            continue
        if _is_hq_metadata_line(s):
            continue
        if _is_non_place_result_line(s) or _BEST_RESERVE_SECTION_RE.match(s):
            flush()
            header = ""
            continue
        if re.match(
            r"(?i)^(?:Conformation|Racing|Go-?to-?Ground|Agility|Obedience|"
            r"Working(?:\s+Terrier)?)\s+DIVISION\b",
            s,
        ):
            flush()
            header = ""
            continue
        m = re.match(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:", s)
        if m:
            rank = int(m.group(1))
            if 1 <= rank <= 12:
                if place_ranks and rank <= place_ranks[-1][0]:
                    flush()
                place_ranks.append((rank, idx, s))
            continue
        if _looks_like_class_header_line(s) or _SECTIONISH_RE.search(s):
            flush()
            header = s[:80]
            continue
    flush()
    return gaps


def pdf_pages(pdf: Path) -> dict[int, str]:
    doc = fitz.open(pdf)
    return {i + 1: doc.load_page(i).get_text("text") for i in range(doc.page_count)}


def page_has_dog(page_text: str, key: str) -> bool:
    if len(key) < 4:
        return False
    # tolerate mild OCR variance: require first token + another token
    toks = [t for t in re.split(r"[^a-z0-9]+", key.lower()) if len(t) >= 3]
    if not toks:
        return False
    low = page_text.lower()
    if key.lower()[:18] in low:
        return True
    return all(any(t in low for t in toks[:2]) for _ in [0]) and toks[0] in low


def hq_page_near(lines: list[str], idx: int) -> int | None:
    for j in range(idx, -1, -1):
        m = PAGE_RE.match(lines[j].strip())
        if m:
            return int(m.group(1))
    return None


def _match_dog(text: str, key: str) -> int:
    """Return start index of dog key in text, or -1."""
    low = text.lower()
    # Prefer longest contiguous key prefix
    for n in (24, 18, 12):
        if len(key) >= max(8, n // 2):
            i = low.find(key[:n])
            if i >= 0:
                return i
    toks = [t for t in re.split(r"[^a-z0-9]+", key) if len(t) >= 4]
    if not toks:
        return -1
    # Require ALL tokens within a short window (avoids East Grinstead Harry ~ Jericho)
    span = min(80, 12 + 10 * len(toks))
    start = 0
    while True:
        i = low.find(toks[0], start)
        if i < 0:
            return -1
        window = low[i : i + span]
        if all(t in window for t in toks):
            return i
        start = i + 1


def places_between_neighbors(
    page_text: str, ka: str, kb: str, missing: list[int]
) -> dict[int, str]:
    """Return cleaned bodies for missing ranks strictly between neighbor dogs in page text."""
    ia = _match_dog(page_text, ka)
    ib = _match_dog(page_text, kb)
    if ia < 0 or ib < 0 or ib <= ia:
        return {}
    window = page_text[ia:ib]
    # Reject huge cross-class windows (neighbors co-page but different classes)
    if len(window) > 500:
        return {}
    places = parse_pdf_places(window)
    out: dict[int, str] = {}
    for r, body in places:
        if r not in missing:
            continue
        cleaned = clean_body(body)
        if cleaned:
            out[r] = cleaned
    if not out and len(missing) == 1:
        owned_lines = []
        for ln in window.splitlines():
            s = ln.strip()
            if not s or re.match(r"(?i)^\d*(?:st|nd|rd|th)\s*:?\s*$", s):
                continue
            if _match_dog(s, ka) >= 0:
                continue
            cleaned = clean_body(s)
            if cleaned:
                owned_lines.append(cleaned)
            else:
                m = re.match(r"(?i)^(?:\d+\s*(?:st|nd|rd|th)|[l1I]st)\s*:?\s*(.+)$", s)
                if m:
                    cleaned = clean_body(m.group(1))
                    if cleaned:
                        owned_lines.append(cleaned)
        uniq = []
        for x in owned_lines:
            if x not in uniq:
                uniq.append(x)
        if len(uniq) == 1:
            out[missing[0]] = uniq[0]
    return out


def recover_from_pdf(text: str, pdf: Path | None, log: Log) -> str:
    if not pdf or not pdf.exists():
        log.notes.append("no year-matched PDF")
        lines = text.splitlines()
        for g in find_gap_blocks(lines):
            log.parked_sidecar.append(
                f"NO_PDF {g['header'][:50]} missing {g['missing']} after {g['sa'][:50]}"
            )
        return text

    pages = pdf_pages(pdf)
    lines = text.splitlines()
    gaps = find_gap_blocks(lines)
    for g in sorted(gaps, key=lambda x: x["ia"], reverse=True):
        ka = dog_key(g["sa"])
        kb = dog_key(g["sb"])
        hq_page = hq_page_near(lines, g["ia"])
        # Candidate PDF pages: HQ page ±2 first; else pages with both neighbors
        cand: list[int] = []
        if hq_page:
            for d in range(0, 3):
                for p in filter(None, [hq_page + d, hq_page - d if d else None]):
                    if p in pages and p not in cand:
                        cand.append(p)
        both = [
            pno
            for pno, pt in pages.items()
            if page_has_dog(pt, ka) and page_has_dog(pt, kb)
        ]
        # Prefer intersection of near-HQ and both; else both restricted to <=3 pages
        ranked = [p for p in cand if p in both] or ([p for p in both if hq_page and abs(p - hq_page) <= 3]) or []
        if not ranked and len(both) == 1:
            ranked = both
        if not ranked:
            log.parked_sidecar.append(
                f"UNSCANNABLE {g['header'][:50]} missing {g['missing']} "
                f"between {g['sa'][:40]} and {g['sb'][:40]} "
                f"(hq_page={hq_page}, both_pages={both[:8]})"
            )
            continue
        recovered: dict[int, str] = {}
        used_page = None
        for pno in ranked:
            got = places_between_neighbors(pages[pno], ka, kb, g["missing"])
            if got:
                recovered = got
                used_page = pno
                break
        if not recovered:
            log.parked_sidecar.append(
                f"UNSCANNABLE {g['header'][:50]} missing {g['missing']} "
                f"on PDF candidates {ranked[:6]} (no in-order owned-by between neighbors)"
            )
            continue
        insert_at = g["ia"] + 1
        block = [f"{ordinal(r)}: {recovered[r]}" for r in sorted(recovered)]
        lines[insert_at:insert_at] = block
        for r in sorted(recovered):
            log.recovered.append(
                f"{ordinal(r)}: {recovered[r][:70]} | {g['header'][:40]} | pdf p{used_page}"
            )
        still = [r for r in g["missing"] if r not in recovered]
        if still:
            log.parked_sidecar.append(
                f"PARTIAL {g['header'][:50]} still missing {still} after recover {list(recovered)}"
            )
    return "\n".join(lines)


def fix_glued(text: str, log: Log, known: dict[str, tuple[str, str]] | None = None) -> str:
    """Split glued ordinals; apply known PDF completions when provided."""
    known = known or {}
    out = []
    for ln in text.splitlines():
        m = re.match(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:\s*(.+)$", ln)
        if not m:
            out.append(ln)
            continue
        r1 = int(m.group(1))
        rest = m.group(2)
        gm = re.search(r"(?i)(.+?)(\d+)(?:st|nd|rd|th)\s*:\s*(.+)$", rest)
        if not gm:
            out.append(ln)
            continue
        left = gm.group(1).strip().rstrip(",;")
        r2 = int(gm.group(2))
        right = gm.group(3).strip()
        key = left.lower()[:24]
        if key in known:
            left_full, right_full = known[key]
            line1 = f"{ordinal(r1)}: {left_full}"
            line2 = f"{ordinal(r2)}: {right_full}"
        else:
            # Only split if right has owned/handled by (evidence of full second place)
            if not re.search(r"(?i)owned by|handled by", right) and "," not in right:
                out.append(ln)
                continue
            # left may be truncated; keep as-is only if it already has owned by,
            # otherwise leave glued for PDF known map / park
            if not re.search(r"(?i)owned by|handled by", left):
                log.parked_sidecar.append(
                    f"GLUED_TRUNC left incomplete, needs PDF name: {ln[:100]}"
                )
                out.append(ln)
                continue
            line1 = f"{ordinal(r1)}: {left}"
            line2 = f"{ordinal(r2)}: {right}"
        out.append(line1)
        out.append(line2)
        log.glued.append(f"{ln[:70]} => {line1} | {line2}")
    return "\n".join(out)


# Verified PDF completions (1990 Vol2 p14): Heckle / Penny
KNOWN_GLUED_1990 = {
    "east grinstead hec": (
        "East Grinstead Heckle, owned by Vail Juhring",
        "Wynnewood Penny, owned by Bill Jacob",
    ),
}


def process(year: int, file: str) -> Log:
    log = Log(year=year, file=file)
    hq = find_hq(year, file)
    if not hq:
        log.notes.append("hq missing")
        return log
    log.hq = str(hq)
    text = hq.read_text(encoding="utf-8", errors="replace")
    log.before = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=120) if c in TARGET)
    bak = Path(str(hq) + ".pre_jr54_recover")
    if not bak.exists():
        shutil.copy2(hq, bak)

    pdf = find_pdf(year, hq)
    log.pdf = str(pdf) if pdf else ""
    known = KNOWN_GLUED_1990 if year == 1990 else {}
    text = fix_glued(text, log, known)
    text = recover_from_pdf(text, pdf, log)
    if not text.endswith("\n"):
        text += "\n"
    hq.write_text(text, encoding="utf-8")

    upd = find_updated_hq(year, hq)
    if upd:
        upd.write_text(text, encoding="utf-8")
        log.notes.append(f"synced {upd}")
    else:
        log.notes.append("Updated HQ mirror not found for year")

    log.after = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=120) if c in TARGET)

    park = hq.with_name(hq.name.replace("_ocr_hqmax.txt", "_PARKED_jr54.txt"))
    park.write_text(
        "JR-54 sidecar park/recover log (gaps that remain stay FAIL in HQ)\n"
        f"hq: {hq}\npdf: {pdf}\nbefore: {log.before} after: {log.after}\n\n"
        "RECOVERED:\n"
        + "\n".join(f"- {x}" for x in log.recovered)
        + "\n\nGLUED:\n"
        + "\n".join(f"- {x}" for x in log.glued)
        + "\n\nUNSCANNABLE/PARTIAL (still FAIL):\n"
        + "\n".join(f"- {x}" for x in log.parked_sidecar)
        + "\n",
        encoding="utf-8",
    )
    return log


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    dem = json.loads(Path("_jr54_demote_counts.json").read_text(encoding="utf-8"))
    rows = [d for d in dem["demoted"] if d["year"] in args.years]
    if args.limit:
        rows = rows[: args.limit]
    reports = []
    for d in rows:
        print(f"\n### {d['year']} {d['file']}", flush=True)
        log = process(d["year"], d["file"])
        print(
            f"hits {log.before}->{log.after} recovered={len(log.recovered)} "
            f"glued={len(log.glued)} parked={len(log.parked_sidecar)}",
            flush=True,
        )
        for r in log.recovered[:6]:
            print(" +", r, flush=True)
        for g in log.glued[:4]:
            print(" ~", g, flush=True)
        for n in log.notes:
            print(" ", n, flush=True)
        reports.append(asdict(log))
    out = Path(f"_jr54_recover_v2_{'_'.join(map(str, args.years))}.json")
    out.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print("WROTE", out)


if __name__ == "__main__":
    main()
