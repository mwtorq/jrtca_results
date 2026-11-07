#!/usr/bin/env python3
"""Scrape jrtcayearbook.com Bronze Medallions + Working Achievement (live + Wayback)
into sResults.NHC. Also capture any Trial Certificate listings into TrialCertificates.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import pyodbc
from bs4 import BeautifulSoup

from remount_source_divisions import CONN
from truegrit_ingest import ensure_dog, ensure_owner
from yearbook_meta_ingest import next_id
import truegrit_schema

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
CACHE = ROOT / "jrtca_org_archive" / "yearbook_certs"
UA = {"User-Agent": "Mozilla/5.0 jrtca-results-research", "Accept-Encoding": "identity"}

LIVE_BRONZE = [
    f"https://www.jrtcayearbook.com/bronze-medallions/bronze-medallions-for-{y}/"
    for y in range(2018, 2026)
] + [
    f"https://www.jrtcayearbook.com/bronze-medallions/bronze-medallions-{y}/"
    for y in (2016, 2017)
]

LIVE_WA = [
    f"https://www.jrtcayearbook.com/working-achievement-awards/working-achievement-awards-for-{y}/"
    for y in range(2021, 2026)
] + [
    f"https://www.jrtcayearbook.com/working-achievement-awards/working-achievement-awards-{y}/"
    for y in range(2016, 2021)
]

_QUARRY = {
    "groundhog",
    "opossum",
    "raccoon",
    "nutria",
    "red fox",
    "fox",
    "woodchuck",
    "badger",
    "coyote",
    "rat",
}
_OWNED_BY = re.compile(
    r"^\s*(.+?)\s+owned by\s+(.+?)\s*$",
    re.I,
)
_YEAR_RE = re.compile(r"(?:for[- ]|awards[- ]|medallions[- ]?)?(20\d{2})", re.I)


@dataclass
class AwardHit:
    dog: str
    owner: str
    quarries: list[str]
    year: int | None
    kind: str  # Bronze Medallion | Working Achievement Award | Trial | NHC
    source: str
    trial_name: str | None = None
    judge: str | None = None


def fetch(url: str, timeout: int = 60) -> tuple[str, str]:
    """Return (final_url, html). Prefer plain Wayback over id_."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        final = r.geturl()
    # strip wayback toolbar if present
    text = raw.decode("utf-8", "ignore")
    return final, text


def cache_path(url: str, prefix: str = "live") -> Path:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", url)[-180:]
    return CACHE / f"{prefix}_{safe}.html"


def get_cached(url: str, prefix: str = "live", force: bool = False) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = cache_path(url, prefix)
    if path.exists() and not force and path.stat().st_size > 500:
        return path.read_text(encoding="utf-8", errors="replace")
    try:
        final, html = fetch(url)
    except Exception as e:
        print(f"  FETCH FAIL {url}: {e}", flush=True)
        return ""
    path.write_text(html, encoding="utf-8", errors="replace")
    meta = path.with_suffix(".meta.txt")
    meta.write_text(f"url={url}\nfinal={final}\n", encoding="utf-8")
    time.sleep(0.6)
    return html


def year_from_url_or_title(url: str, soup: BeautifulSoup) -> int | None:
    # Prefer year in the original path slug, not the Wayback timestamp.
    orig = url
    m_wb = re.search(r"/web/\d{14}/(?:https?://)?(.+)$", url, re.I)
    if m_wb:
        orig = m_wb.group(1)
    for pat in (
        r"bronze-medallions-(?:for-)?(20\d{2})",
        r"working-achievement-awards-(?:for-)?(20\d{2})",
        r"(?:medallions|awards)[^0-9]{0,12}(20\d{2})",
    ):
        m = re.search(pat, orig, re.I)
        if m:
            return int(m.group(1))
    h1 = soup.find(["h1", "h2"])
    if h1:
        m = _YEAR_RE.search(h1.get_text(" ", strip=True))
        if m:
            return int(m.group(1))
    # Index pages sometimes only show current award year in heading
    for h in soup.find_all(["h1", "h2", "h3"]):
        m = re.search(
            r"(?:Bronze Medallion|Working Achievement)[^0-9]{0,40}(20\d{2})",
            h.get_text(" ", strip=True),
            re.I,
        )
        if m:
            return int(m.group(1))
    return None


def parse_quarry_tokens(text: str) -> list[str]:
    parts = re.split(r"[\s,;/|]+", text.strip())
    out = []
    i = 0
    while i < len(parts):
        p = parts[i].strip()
        if not p:
            i += 1
            continue
        two = f"{p} {parts[i+1]}".lower() if i + 1 < len(parts) else ""
        if two in _QUARRY:
            out.append(parts[i] + " " + parts[i + 1])
            i += 2
            continue
        if p.lower() in _QUARRY:
            out.append(p.title() if p.lower() != "red fox" else "Red Fox")
            i += 1
            continue
        # skip non-quarry
        i += 1
    # normalize
    normed = []
    for q in out:
        ql = q.lower()
        if ql == "fox":
            ql = "red fox"
        normed.append("Red Fox" if ql == "red fox" else q.title())
    return normed


def parse_award_page(html: str, url: str, kind: str) -> list[AwardHit]:
    """Parse Shortcodes Ultimate column cards:
    <strong>Dog</strong><br/><em>owned by Owner</em></p><p>Quarry<br/>...
    """
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    year = year_from_url_or_title(url, soup)
    root = soup.select_one("article, .entry-content, .post-content, main, #content") or soup
    hits: list[AwardHit] = []

    # Primary: each su-column-inner (or any block with strong + owned-by em)
    containers = root.select(".su-column-inner")
    if not containers:
        # fallback: any parent of strong near owned-by
        containers = []
        for em in root.find_all("em"):
            if "owned by" in em.get_text(" ", strip=True).lower():
                parent = em.find_parent(["div", "p", "td", "li"]) or em.parent
                if parent and parent not in containers:
                    containers.append(parent)

    for box in containers:
        strong = box.find("strong")
        em = box.find("em")
        if not strong or not em:
            continue
        dog = strong.get_text(" ", strip=True)
        owner_txt = em.get_text(" ", strip=True)
        m = re.match(r"owned by\s+(.+)$", owner_txt, re.I)
        if not m:
            continue
        owner = m.group(1).strip()
        # Drop "/bred by …" suffixes that appear on some cards
        owner = re.split(r"\s*/\s*bred by\s+", owner, flags=re.I)[0].strip()
        # quarries: following <p> siblings inside box that are not empty
        quarry_bits: list[str] = []
        # after the em's parent p, subsequent p tags
        for p in box.find_all("p"):
            # skip the p that only wraps the name/owner
            if p.find("strong") or p.find("em"):
                continue
            raw = p.get_text("\n", strip=True)
            if not raw:
                continue
            quarry_bits.extend(parse_quarry_tokens(raw.replace("\n", " ")))
        # also collect bare text lines under box
        if not quarry_bits:
            text = box.get_text("\n", strip=True)
            # remove dog/owner lines
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            rest = []
            for ln in lines:
                if ln == dog or ln.lower().startswith("owned by"):
                    continue
                rest.append(ln)
            quarry_bits = parse_quarry_tokens(" ".join(rest))

        if len(dog) < 3 or len(owner) < 3:
            continue
        if re.search(r"Bronze Medallion|Working Achievement|Trial Results", dog, re.I):
            continue
        hits.append(
            AwardHit(
                dog=dog[:255],
                owner=owner[:255],
                quarries=quarry_bits,
                year=year,
                kind=kind,
                source=url,
            )
        )

    # Fallback regex over cleaned HTML text for older pages
    if not hits:
        text = root.get_text("\n", strip=True)
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]
        i = 0
        while i < len(lines):
            # Dog on one line, "owned by X" next
            if i + 1 < len(lines) and lines[i + 1].lower().startswith("owned by "):
                dog = lines[i]
                owner = lines[i + 1][len("owned by ") :].strip()
                j = i + 2
                qlines = []
                while j < len(lines) and lines[j].lower() in _QUARRY | {"red fox"}:
                    qlines.append(lines[j])
                    j += 1
                # or a single line of quarries
                if not qlines and j < len(lines):
                    qs = parse_quarry_tokens(lines[j])
                    if qs:
                        qlines = qs
                        j += 1
                if len(dog) >= 3 and owner and not re.search(r"Medallion|Achievement", dog, re.I):
                    hits.append(
                        AwardHit(
                            dog=dog[:255],
                            owner=owner[:255],
                            quarries=[q.title() if q.lower() != "red fox" else "Red Fox" for q in qlines],
                            year=year,
                            kind=kind,
                            source=url,
                        )
                    )
                i = j
                continue
            i += 1

    seen = set()
    out = []
    for h in hits:
        k = (h.dog.lower(), h.owner.lower(), h.year, h.kind)
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


def cdx_list(url_pattern: str, limit: int = 100) -> list[tuple[str, str]]:
    q = (
        "https://web.archive.org/cdx/search/cdx?"
        f"url={urllib.request.quote(url_pattern)}&output=json"
        "&fl=timestamp,original,statuscode&filter=statuscode:200"
        f"&limit={limit}&collapse=digest"
    )
    try:
        req = urllib.request.Request(q, headers=UA)
        with urllib.request.urlopen(req, timeout=90) as r:
            rows = json.load(r)
    except Exception as e:
        print(f"CDX FAIL {url_pattern}: {e}", flush=True)
        return []
    out = []
    for row in rows[1:]:
        ts, orig = row[0], row[1]
        out.append((ts, orig))
    return out


def wayback_url(ts: str, orig: str) -> str:
    # plain replay (not id_)
    return f"https://web.archive.org/web/{ts}/{orig}"


def collect_pages() -> list[tuple[str, str, str]]:
    """Return list of (kind, prefix, url) to fetch."""
    pages: list[tuple[str, str, str]] = []
    for u in LIVE_BRONZE:
        pages.append(("Bronze Medallion", "live", u))
    for u in LIVE_WA:
        pages.append(("Working Achievement Award", "live", u))

    # Wayback: bronze + working achievement path wildcards
    for pat, kind in (
        ("jrtcayearbook.com/bronze-medallions/*", "Bronze Medallion"),
        ("www.jrtcayearbook.com/bronze-medallions/*", "Bronze Medallion"),
        ("jrtcayearbook.com/working-achievement-awards/*", "Working Achievement Award"),
        ("www.jrtcayearbook.com/working-achievement-awards/*", "Working Achievement Award"),
        ("jrtcayearbook.com/*trial*cert*", "Trial"),
        ("www.jrtcayearbook.com/*trial*cert*", "Trial"),
        ("jrtcayearbook.com/*nhc*", "NHC"),
        ("www.jrtcayearbook.com/*nhc*", "NHC"),
    ):
        for ts, orig in cdx_list(pat, limit=80):
            # skip pure index if we already have live; still fetch year pages
            wu = wayback_url(ts, orig)
            pages.append((kind, f"wb{ts}", wu))
            time.sleep(0.25)
    # dedupe by URL
    seen = set()
    out = []
    for kind, prefix, url in pages:
        if url in seen:
            continue
        seen.add(url)
        out.append((kind, prefix, url))
    return out


def apply_hits(cur, hits: list[AwardHit], *, apply: bool) -> dict:
    stats = {"nhc": 0, "trial_cert": 0, "skip": 0}
    for h in hits:
        if not h.year:
            stats["skip"] += 1
            continue
        owner_id = ensure_owner(cur, h.owner, apply=apply)
        note = f"jrtcayearbook.com {h.kind} ({h.year})"
        dog_id = ensure_dog(
            cur,
            h.dog,
            owner_id,
            apply=apply,
            note=note,
            source=f"yearbook:{h.source}",
        )

        if h.kind in {"Bronze Medallion", "Working Achievement Award", "NHC"}:
            quarries = h.quarries or ["(unspecified)"]
            # distinct quarries for upsert key stability
            seen_q = set()
            for q in quarries:
                qn = q.strip()
                key = qn.lower()
                if key in seen_q:
                    continue
                seen_q.add(key)
                cert_type = h.kind
                if h.kind == "NHC":
                    cert_type = "Natural Hunting Certificate"
                notes = f"{h.kind} from jrtcayearbook.com ({h.year})"
                if h.quarries:
                    notes += "; quarries listed: " + ", ".join(h.quarries)
                stats["nhc"] += 1
                if not apply:
                    continue
                cur.execute(
                    """
                    SELECT NHCID FROM sResults.NHC
                    WHERE DogName=? AND ISNULL(OwnerName,'')=ISNULL(?, '')
                      AND ISNULL(Prey,'')=ISNULL(?, '')
                      AND ISNULL(CertificateType,'')=ISNULL(?, '')
                      AND ISNULL(Year,0)=?
                    """,
                    h.dog[:255],
                    h.owner[:255],
                    qn[:100],
                    cert_type[:100],
                    h.year,
                )
                if cur.fetchone():
                    continue
                nid = next_id(cur, "NHC", "NHCID")
                cur.execute(
                    """
                    INSERT INTO sResults.NHC
                    (NHCID, Year, DogName, DogID, OwnerName, OwnerID, CertificateType, Prey, Notes, SourcePath)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    nid,
                    h.year,
                    h.dog[:255],
                    dog_id,
                    h.owner[:255],
                    owner_id,
                    cert_type[:100],
                    qn[:100],
                    notes[:2000],
                    h.source[:1000],
                )
        elif h.kind == "Trial":
            stats["trial_cert"] += 1
            if not apply:
                continue
            cur.execute(
                """
                SELECT TrialCertificateID FROM sResults.TrialCertificates
                WHERE DogName=? AND ISNULL(OwnerName,'')=ISNULL(?, '')
                  AND ISNULL(TrialName,'')=ISNULL(?, '')
                  AND ISNULL(CertificateType,'')=ISNULL(?, '')
                  AND ISNULL(Year,0)=?
                """,
                h.dog[:255],
                h.owner[:255],
                (h.trial_name or "")[:255],
                "Trial",
                h.year,
            )
            if cur.fetchone():
                continue
            tid = next_id(cur, "TrialCertificates", "TrialCertificateID")
            cur.execute(
                """
                INSERT INTO sResults.TrialCertificates
                (TrialCertificateID, Year, DogName, DogID, OwnerName, OwnerID,
                 JudgeName, TrialName, CertificateType, Notes, SourcePath)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                tid,
                h.year,
                h.dog[:255],
                dog_id,
                h.owner[:255],
                owner_id,
                h.judge,
                h.trial_name,
                "Trial",
                f"Trial certificate from jrtcayearbook.com ({h.year})"[:2000],
                h.source[:1000],
            )
        else:
            stats["skip"] += 1
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-wayback", action="store_true")
    ap.add_argument("--force-fetch", action="store_true")
    args = ap.parse_args(argv)

    pages = []
    for u in LIVE_BRONZE:
        pages.append(("Bronze Medallion", "live", u))
    for u in LIVE_WA:
        pages.append(("Working Achievement Award", "live", u))
    if not args.no_wayback:
        print("CDX Wayback inventory…", flush=True)
        for pat, kind in (
            ("jrtcayearbook.com/bronze-medallions/*", "Bronze Medallion"),
            ("www.jrtcayearbook.com/bronze-medallions/*", "Bronze Medallion"),
            ("jrtcayearbook.com/working-achievement-awards/*", "Working Achievement Award"),
            ("www.jrtcayearbook.com/working-achievement-awards/*", "Working Achievement Award"),
        ):
            rows = cdx_list(pat, limit=60)
            print(f"  {pat}: {len(rows)}", flush=True)
            # keep up to 2 captures per original URL (oldest+newest-ish via collapse=digest)
            by_orig: dict[str, list[str]] = {}
            for ts, orig in rows:
                by_orig.setdefault(orig, []).append(ts)
            for orig, tss in by_orig.items():
                tss = sorted(set(tss))
                pick = {tss[0], tss[-1]}
                for ts in pick:
                    pages.append((kind, f"wb{ts}", wayback_url(ts, orig)))

    seen_u = set()
    uniq_pages = []
    for kind, prefix, url in pages:
        if url in seen_u:
            continue
        seen_u.add(url)
        uniq_pages.append((kind, prefix, url))

    all_hits: list[AwardHit] = []
    for kind, prefix, url in uniq_pages:
        print(f"GET [{kind}] {url}", flush=True)
        html = get_cached(url, prefix=prefix, force=args.force_fetch)
        if not html:
            continue
        hits = parse_award_page(html, url, kind)
        print(f"  parsed {len(hits)} awards year~{hits[0].year if hits else None}", flush=True)
        all_hits.extend(hits)

    # summary
    by_kind: dict[str, int] = {}
    for h in all_hits:
        by_kind[h.kind] = by_kind.get(h.kind, 0) + 1
    print("TOTAL hits", len(all_hits), by_kind, flush=True)

    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    _truegrit_schema.ensure(cur)
    cn.commit()
    stats = apply_hits(cur, all_hits, apply=args.apply)
    if args.apply:
        cn.commit()
        print("COMMITTED", stats, flush=True)
    else:
        cn.rollback()
        print("DRY-RUN", stats, flush=True)
    cn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
