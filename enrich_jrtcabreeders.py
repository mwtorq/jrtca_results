#!/usr/bin/env python3
"""Post-process jrtcabreeders load: junk/misnamed dogs, title case, missing kennels."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from scrape_jrtcabreeders import (
    EMAIL_RE,
    PHONE_RE,
    SCRAPE_INSERT_MIN_ID,
    ST_RE,
    ZIP_RE,
    clip,
    fill_if_empty,
    get_conn,
    is_junk_row_name,
    looks_like_dog_name,
    merge_text,
    normalize_key,
)

JUNK_HEADER = re.compile(
    r"(home page|jack russells?$|pups?$|puppies|trio of|a few .+ puppies|"
    r"x .+ puppies|code of ethics|introduction)",
    re.I,
)
ADDR_NAME = re.compile(
    r"\d{3,}.+\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|"
    r"MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|"
    r"VA|VT|WA|WI|WV|WY)\b.+\d{5}",
    re.I,
)
SMALL = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to", "x"}
SKIP_PREFIX = {
    "the", "a", "an", "of", "and", "our", "my", "latest", "introducing",
    "unknown", "n/a", "none", "dog", "bitch", "male", "female",
}


def cap_word(word: str) -> str:
    if not word:
        return word
    if word in {"&", "/", "-"}:
        return word
    parts = re.split(r"(['’\-])", word)
    out = []
    for p in parts:
        if p in {"'", "’", "-"} or not p:
            out.append(p)
        else:
            out.append(p[0].upper() + p[1:].lower())
    return "".join(out)


def title_dog_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return n
    letters = [c for c in n if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < 0.75:
        return n
    low = re.sub(r"\s+", " ", n)
    prefix = ""
    rest = low
    if re.match(r"^NOMA\b", rest, re.I):
        prefix = "NOMA"
        rest = rest[4:].strip()
    elif re.match(r"^R\s*&\s*B\b", rest, re.I):
        prefix = "R&B"
        rest = re.sub(r"^R\s*&\s*B\b", "", rest, flags=re.I).strip()
    elif re.match(r"^J\s*&\s*J\b", rest, re.I):
        prefix = "J & J"
        rest = re.sub(r"^J\s*&\s*J\b", "", rest, flags=re.I).strip()
    words = rest.split() if rest else []
    titled = [cap_word(w) for w in words]
    if prefix and titled:
        return prefix + " " + " ".join(titled)
    if prefix:
        return prefix
    return " ".join(titled)


def merge_into(cur, src_id: int, dest_id: int, updates: dict) -> None:
    fill_if_empty(cur, "Dog", "DogID", dest_id, updates)
    if updates.get("Notes"):
        cur.execute("SELECT Notes FROM sResults.Dog WHERE DogID=?", dest_id)
        row = cur.fetchone()
        cur.execute(
            "UPDATE sResults.Dog SET Notes=? WHERE DogID=?",
            merge_text(row[0] if row else None, updates.get("Notes")),
            dest_id,
        )
    cur.execute(
        """
        UPDATE sResults.Relationship SET DogID=?
        WHERE DogID=? AND NOT EXISTS (
            SELECT 1 FROM sResults.Relationship r
            WHERE r.DogID=? AND r.RelatedDogName=sResults.Relationship.RelatedDogName
              AND r.RelationshipType=sResults.Relationship.RelationshipType
        )
        """,
        dest_id,
        src_id,
        dest_id,
    )
    cur.execute("DELETE FROM sResults.Relationship WHERE DogID=? OR RelatedDogID=?", src_id, src_id)
    cur.execute("DELETE FROM sResults.Dog WHERE DogID=?", src_id)


def fix_junk_and_misnamed(cur) -> dict:
    stats = {"deleted": 0, "merged": 0, "renamed": 0}
    cur.execute("SELECT DogID, Sire, Dam, Height, Coat, Color, Notes, SourceURL, BreederID FROM sResults.Dog WHERE DogID=1263814")
    ruckus = cur.fetchone()
    if ruckus:
        merge_into(
            cur,
            1263814,
            1078297,
            {
                "Sire": ruckus[1],
                "Dam": ruckus[2],
                "Height": ruckus[3],
                "Coat": ruckus[4],
                "Color": ruckus[5],
                "Notes": ruckus[6],
                "SourceURL": ruckus[7],
                "BreederID": 87,
            },
        )
        stats["merged"] += 1
    cur.execute("SELECT DogID, Sire, Dam, Height, Coat, Color, Notes, SourceURL FROM sResults.Dog WHERE DogID=1263816")
    luke = cur.fetchone()
    if luke:
        merge_into(
            cur,
            1263816,
            1078655,
            {
                "Sire": luke[1],
                "Dam": luke[2],
                "Height": luke[3],
                "Coat": luke[4],
                "Color": luke[5],
                "Notes": luke[6],
                "SourceURL": luke[7],
                "BreederID": 89,
            },
        )
        stats["merged"] += 1

    cur.execute(
        """
        SELECT DogID, DogName, Sire, Dam FROM sResults.Dog
        WHERE DogID >= ?
        """,
        SCRAPE_INSERT_MIN_ID,
    )
    delete_ids = []
    for did, name, sire, dam in cur.fetchall():
        n = name or ""
        if did in {1263814, 1263816}:
            continue
        if ADDR_NAME.search(n) or JUNK_HEADER.search(n) or is_junk_row_name(n):
            if sire or dam:
                continue
            delete_ids.append(did)
    if delete_ids:
        marks = ",".join("?" * len(delete_ids))
        cur.execute(
            f"DELETE FROM sResults.Relationship WHERE DogID IN ({marks}) OR RelatedDogID IN ({marks})",
            delete_ids + delete_ids,
        )
        cur.execute(f"DELETE FROM sResults.Dog WHERE DogID IN ({marks})", delete_ids)
        stats["deleted"] = cur.rowcount or 0

    for bid in (48, 50, 51):
        cur.execute("UPDATE sResults.Dog SET BreederID=NULL WHERE BreederID=?", bid)
        cur.execute("DELETE FROM sResults.Breeder WHERE BreederID=?", bid)
    return stats


def title_case_new_dogs(cur) -> int:
    cur.execute(
        "SELECT DogID, DogName FROM sResults.Dog WHERE DogID >= ?",
        SCRAPE_INSERT_MIN_ID,
    )
    n = 0
    for did, name in cur.fetchall():
        new = title_dog_name(name or "")
        if new and new != name:
            cur.execute("UPDATE sResults.Dog SET DogName=? WHERE DogID=?", new[:255], did)
            n += 1
    return n


def name_tokens(name: str) -> list[str]:
    n = (name or "").strip()
    if re.match(r"^NOMA\b", n, re.I):
        rest = n[4:].strip()
        return ["NOMA"] + ([w for w in rest.split() if w] if rest else [])
    if re.match(r"^R\s*&\s*B\b", n, re.I):
        rest = re.sub(r"^R\s*&\s*B\b", "", n, flags=re.I).strip()
        return ["R&B"] + ([w for w in rest.split() if w] if rest else [])
    if re.match(r"^J\s*&\s*J\b", n, re.I):
        rest = re.sub(r"^J\s*&\s*J\b", "", n, flags=re.I).strip()
        return ["J & J"] + ([w for w in rest.split() if w] if rest else [])
    return [w for w in re.split(r"\s+", n) if w]


def ngram(tokens: list[str], n: int) -> str:
    return " ".join(tokens[:n])


KENNEL_TAILS = {
    "farm", "farms", "acres", "hill", "hills", "hall", "creek", "ranch", "ridge",
    "grove", "range", "street", "bottom", "valley", "view", "springs", "spring",
    "hollow", "landing", "kennels", "park", "place", "woods", "wood", "oaks",
    "moon", "gate", "point", "mill", "meadow", "glen", "dale", "haven", "crest",
    "corner", "crossing", "branch", "brook", "bluff", "knoll", "lodge", "manor",
}


def distinct_call_names(hits: list[tuple[str, str | None]], prefix: str) -> set[str]:
    pre = prefix.lower()
    calls = set()
    for name, _ in hits:
        n = (name or "").strip()
        if n.lower() == pre:
            continue
        if n.lower().startswith(pre + " "):
            call = n[len(prefix) :].strip()
            if call:
                calls.add(normalize_key(call))
    return calls


def fold_kennel(name: str) -> str:
    n = (name or "").lower().replace("'", "").replace("'", "").replace("`", "")
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def covered_by_existing(name: str, have_folds: dict) -> bool:
    key = fold_kennel(name)
    if not key:
        return True
    if key in have_folds:
        return True
    for h in have_folds:
        if h.startswith(key + " ") or key.startswith(h + " "):
            return True
    return False


def looks_like_kennel_prefix(prefix: str) -> bool:
    words = prefix.split()
    if len(words) < 2 and prefix not in {"NOMA", "R&B", "J & J"}:
        return False
    if words[-1].lower() in {"of", "the", "and", "x"}:
        return False
    if re.search(r"\d", prefix):
        return False
    return True


def extrapolate_missing_kennels(cur) -> list[dict]:
    """Multi-word prefixes shared by several distinct dogs: Trails End, not Trails."""
    cur.execute("SELECT BreederID, KennelName, OwnerName FROM sResults.Breeder")
    have = {
        fold_kennel(n): (bid, n, own)
        for bid, n, own in cur.fetchall()
        if n and fold_kennel(n)
    }
    cur.execute(
        """
        SELECT d.DogName, o.OwnerName
        FROM sResults.Dog d
        LEFT JOIN sResults.Owner o ON d.OwnerID = o.OwnerID
        WHERE d.DogName IS NOT NULL AND LEN(d.DogName) > 3
        """
    )
    tokenized: list[tuple[list[str], str, str | None]] = []
    c2: Counter = Counter()
    c3: Counter = Counter()
    for dname, oname in cur.fetchall():
        toks = name_tokens(dname)
        if not toks or toks[0].lower().strip(".,") in SKIP_PREFIX:
            continue
        tokenized.append((toks, dname, oname))
        if len(toks) >= 2:
            c2[fold_kennel(ngram(toks, 2))] += 1
        if len(toks) >= 3:
            c3[fold_kennel(ngram(toks, 3))] += 1

    # Collect candidate prefixes with distinct dog tails + owner votes
    cand: dict[str, dict] = {}
    for toks, dname, oname in tokenized:
        options = []
        if len(toks) >= 3:
            p3 = ngram(toks, 3)
            if (
                looks_like_kennel_prefix(p3)
                and toks[2].lower().rstrip("s") in KENNEL_TAILS
                and c3[fold_kennel(p3)] >= 4
            ):
                options.append(p3)
        if len(toks) >= 2:
            p2 = ngram(toks, 2)
            if looks_like_kennel_prefix(p2) and c2[fold_kennel(p2)] >= 5:
                options.append(p2)
        if not options:
            continue
        # Prefer 2-word kennel (Bear Trace), not kennel+dog (Bear Trace Ames)
        picked = min(options, key=lambda p: (len(p.split()), -len(p)))
        key = fold_kennel(picked)
        slot = cand.setdefault(
            key,
            {"display": Counter(), "calls": set(), "owners": Counter(), "n": 0},
        )
        slot["display"][picked] += 1
        slot["n"] += 1
        if dname.lower().startswith(picked.lower() + " "):
            slot["calls"].add(normalize_key(dname[len(picked) :].strip()))
        elif normalize_key(dname) != normalize_key(picked):
            slot["calls"].add(normalize_key(dname))
        if oname and len(oname.strip()) > 3 and "@" not in oname and "http" not in oname.lower():
            slot["owners"][oname.strip()] += 1

    # Drop shorter prefixes when a longer candidate exists (Trails vs Trails End)
    keys = list(cand.keys())
    for short in keys:
        for long in keys:
            if short != long and long.startswith(short + " "):
                cand.pop(short, None)
                break

    missing = []
    for key, slot in cand.items():
        kennel_disp = slot["display"].most_common(1)[0][0]
        if covered_by_existing(kennel_disp, have):
            continue
        if len(slot["calls"]) < 4:
            continue
        owner = None
        owner_n = 0
        if slot["owners"]:
            owner, owner_n = slot["owners"].most_common(1)[0]
            if owner_n < 2:
                owner = None
                owner_n = 0
        missing.append(
            {
                "kennel": kennel_disp,
                "key": key,
                "dogs": slot["n"],
                "calls": len(slot["calls"]),
                "owner": owner,
                "owner_n": owner_n,
            }
        )
    missing.sort(key=lambda x: (-x["calls"], -x["dogs"], x["kennel"]))
    return missing


def drop_bad_extrapolations(cur) -> int:
    """Delete 1-word stubs and spelling dupes (Achin' / Achin Acres / Achin'Acres)."""
    cur.execute(
        """
        SELECT BreederID, KennelName, OwnerName, Notes
        FROM sResults.Breeder
        """
    )
    rows = cur.fetchall()
    extra_ids = []
    keep: dict[str, list[tuple]] = defaultdict(list)
    for bid, name, owner, notes in rows:
        extra = (notes or "").startswith("Extrapolated from")
        words = (name or "").split()
        if extra and (len(words) <= 1 and (name or "") not in {"NOMA", "R&B", "J & J"}):
            fold = fold_kennel(name or "")
            parent = None
            for bid2, name2, owner2, notes2 in rows:
                if bid2 == bid or not name2:
                    continue
                f2 = fold_kennel(name2)
                if f2.startswith(fold + " ") or f2 == fold:
                    parent = bid2
                    if f2.startswith(fold + " "):
                        break
            if parent:
                cur.execute("UPDATE sResults.Dog SET BreederID=? WHERE BreederID=?", parent, bid)
            extra_ids.append(bid)
            continue
        fold = fold_kennel(name or "")
        if not fold:
            continue
        keep[fold].append((bid, name or "", owner or "", extra))

    delete_ids = list(extra_ids)
    for fold, group in keep.items():
        longer = [
            (bid, name, owner, extra)
            for bid, name, owner, extra in group
        ]
        # prefix stub of a longer fold (achin vs achin acres)
        for fold2, group2 in keep.items():
            if fold2 != fold and fold2.startswith(fold + " "):
                for bid, name, owner, extra in group:
                    if extra or len(name.split()) < len(group2[0][1].split()):
                        delete_ids.append(bid)
                break
        if len(group) < 2:
            continue
        group_sorted = sorted(
            group,
            key=lambda r: (
                0 if not r[3] else 1,
                -len(r[1]),
                r[0],
            ),
        )
        winner = group_sorted[0][0]
        for bid, name, owner, extra in group_sorted[1:]:
            cur.execute("UPDATE sResults.Dog SET BreederID=? WHERE BreederID=?", winner, bid)
            cur.execute("UPDATE sResults.Owner SET BreederID=? WHERE BreederID=?", winner, bid)
            delete_ids.append(bid)

    delete_ids = list(dict.fromkeys(delete_ids))
    if not delete_ids:
        return 0
    marks = ",".join("?" * len(delete_ids))
    cur.execute(
        f"""
        UPDATE d SET d.BreederID = NULL
        FROM sResults.Dog d
        WHERE d.BreederID IN ({marks})
        """,
        delete_ids,
    )
    cur.execute(f"DELETE FROM sResults.Breeder WHERE BreederID IN ({marks})", delete_ids)
    return cur.rowcount or 0


def insert_missing_breeders(cur, missing: list[dict]) -> int:
    n = 0
    for rec in missing:
        cur.execute(
            "SELECT BreederID FROM sResults.Breeder WHERE KennelName=?",
            rec["kennel"],
        )
        if cur.fetchone():
            continue
        cur.execute("SELECT KennelName FROM sResults.Breeder")
        have_now = {fold_kennel(r[0]): r[0] for r in cur.fetchall() if r[0]}
        if covered_by_existing(rec["kennel"], have_now):
            continue
        cur.execute(
            """
            INSERT INTO sResults.Breeder (KennelName, KennelPrefix, OwnerName, Notes)
            OUTPUT INSERTED.BreederID
            VALUES (?,?,?,?)
            """,
            rec["kennel"][:255],
            rec["kennel"][:100],
            rec["owner"],
            f"Extrapolated from {rec['dogs']} dog names"
            + (f"; owner seen {rec['owner_n']} times" if rec["owner"] else ""),
        )
        bid = cur.fetchone()[0]
        rec["breeder_id"] = bid
        n += 1
        if " " in rec["kennel"] or rec["kennel"] in {"NOMA", "R&B", "J & J"}:
            prefix = rec["kennel"] + " "
            cur.execute(
                """
                UPDATE d SET d.BreederID = COALESCE(d.BreederID, ?)
                FROM sResults.Dog d
                WHERE d.BreederID IS NULL AND (
                    d.DogName = ? OR d.DogName LIKE ?
                )
                """,
                bid,
                rec["kennel"],
                prefix + "%",
            )
    return n


def apply_web_facts(cur, breeder_id: int, facts: dict) -> None:
    fill_if_empty(
        cur,
        "Breeder",
        "BreederID",
        breeder_id,
        {
            "Address": clip(facts.get("address"), 255),
            "City": clip(facts.get("city"), 100),
            "State": clip(facts.get("state"), 50),
            "PostalCode": clip(facts.get("postal"), 20),
            "Email": clip(facts.get("email"), 255),
            "Phone": clip(facts.get("phone"), 100),
            "Website": clip(facts.get("website"), 500),
            "OwnerName": clip(facts.get("owner"), 255),
        },
    )


HTML_OWNER_RE = re.compile(
    r"[<>]|href|www\.|handwriting|NTER>|LIGN=|/B>|FONT|SIZE=|NHC to|"
    r"Welcome|Jack Russells|Stud Dogs|Always Welcome|inquir|brucellosis|"
    r"CELLPADDING|Zurich BT|Owned by|More of Our|The Girls|Introduction",
    re.I,
)


def owner_is_junk(name: Optional[str]) -> bool:
    if not name or not name.strip():
        return True
    return bool(HTML_OWNER_RE.search(name))


def best_owner_for_kennel(cur, bid: int, kennel: str) -> Optional[str]:
    cur.execute(
        """
        SELECT o.OwnerName, COUNT(*) c
        FROM sResults.Dog d
        INNER JOIN sResults.Owner o ON d.OwnerID = o.OwnerID
        WHERE o.OwnerName IS NOT NULL AND LEN(o.OwnerName) > 3
          AND o.OwnerName NOT LIKE '%@%'
          AND o.OwnerName NOT LIKE '%http%'
          AND o.OwnerName NOT LIKE '%<%'
          AND o.OwnerName NOT LIKE '%>%'
          AND (
                d.BreederID = ?
             OR d.DogName = ?
             OR d.DogName LIKE ?
          )
        GROUP BY o.OwnerName
        ORDER BY c DESC
        """,
        bid,
        kennel,
        kennel + " %",
    )
    for oname, cnt in cur.fetchall():
        if owner_is_junk(oname) or cnt < 2:
            continue
        return oname[:255]
    return None


def fill_missing_owners(cur) -> int:
    """Replace blank/HTML OwnerName from the most common real owner on that kennel's dogs."""
    cur.execute("SELECT BreederID, KennelName, OwnerName FROM sResults.Breeder")
    n = 0
    for bid, kennel, old in cur.fetchall():
        if not kennel:
            continue
        if old and not owner_is_junk(old):
            continue
        owner = best_owner_for_kennel(cur, bid, kennel)
        if not owner:
            if old and owner_is_junk(old):
                cur.execute(
                    "UPDATE sResults.Breeder SET OwnerName=NULL WHERE BreederID=?",
                    bid,
                )
                n += 1
            continue
        cur.execute(
            "UPDATE sResults.Breeder SET OwnerName=? WHERE BreederID=?",
            owner,
            bid,
        )
        n += 1
    return n


def collapse_dogname_kennels(cur) -> int:
    """Bear Trace Ames + Bear Trace Yazoo -> Bear Trace kennel.

    Only when 2+ extrapolated rows share a 2-word prefix and the leftover
    token is a call name (not Farm/Hill/View/Not/Out/etc).
    """
    cur.execute(
        """
        SELECT BreederID, KennelName, OwnerName, Notes
        FROM sResults.Breeder
        WHERE Notes LIKE 'Extrapolated from%'
           OR Notes LIKE 'Collapsed from%'
        """
    )
    extras = cur.fetchall()
    by_prefix: dict[str, list] = defaultdict(list)
    for bid, name, owner, notes in extras:
        words = (name or "").split()
        if len(words) < 3:
            continue
        third = words[2].lower().rstrip("s.,")
        # Real 3-word kennels: Forget Me Not, Point of View, Dig Em Out, Hide Away Farms
        if third in KENNEL_TAILS or third in {
            "not", "out", "view", "dash", "tumble", "jacks", "low", "quick",
            "river", "west", "east", "north", "south",
        }:
            continue
        if words[1].lower() in {"of", "&", "n", "n'", "'n", "o'"}:
            continue
        pref = " ".join(words[:2])
        by_prefix[fold_kennel(pref)].append((bid, name, owner, pref, words[2]))

    collapsed = 0
    for key, group in by_prefix.items():
        # Require multiple distinct call-name tails (Ames vs Yazoo)
        tails = {t.lower() for *_x, t in group}
        if len(tails) < 2:
            continue
        pref = Counter(p for _b, _n, _o, p, _t in group).most_common(1)[0][0]

        # Find or create the real kennel
        cur.execute(
            "SELECT BreederID, KennelName FROM sResults.Breeder WHERE KennelName=? OR KennelName=?",
            pref,
            pref.replace("'", "’"),
        )
        row = cur.fetchone()
        if not row:
            # any existing folded match
            cur.execute("SELECT BreederID, KennelName FROM sResults.Breeder")
            row = next(
                (
                    (bid, name)
                    for bid, name in cur.fetchall()
                    if fold_kennel(name or "") == fold_kennel(pref)
                ),
                None,
            )
        if row:
            parent_id, parent_name = row
        else:
            owner = best_owner_for_kennel(cur, group[0][0], pref)
            cur.execute(
                """
                INSERT INTO sResults.Breeder (KennelName, KennelPrefix, OwnerName, Notes)
                OUTPUT INSERTED.BreederID
                VALUES (?,?,?,?)
                """,
                pref[:255],
                pref[:100],
                owner,
                f"Collapsed from dog-name kennel rows under {pref}",
            )
            parent_id = cur.fetchone()[0]
            parent_name = pref
            print(f"  created kennel {parent_name!r} id={parent_id}")

        for bid, name, owner, _pref, _tail in group:
            if bid == parent_id:
                continue
            cur.execute("UPDATE sResults.Dog SET BreederID=? WHERE BreederID=?", parent_id, bid)
            cur.execute("UPDATE sResults.Owner SET BreederID=? WHERE BreederID=?", parent_id, bid)
            cur.execute("DELETE FROM sResults.Breeder WHERE BreederID=?", bid)
            collapsed += 1
            print(f"  collapse {name!r} -> {parent_name!r}")

        # Link unlinked dogs with that prefix
        cur.execute(
            """
            UPDATE sResults.Dog
            SET BreederID = COALESCE(BreederID, ?)
            WHERE DogName = ? OR DogName LIKE ?
            """,
            parent_id,
            parent_name,
            parent_name + " %",
        )
        owner = best_owner_for_kennel(cur, parent_id, parent_name)
        if owner:
            cur.execute(
                "UPDATE sResults.Breeder SET OwnerName=COALESCE(NULLIF(OwnerName,''), ?) WHERE BreederID=?",
                owner,
                parent_id,
            )
    return collapsed


def breeders_needing_contact(cur, limit: int = 40) -> list[tuple]:
    cur.execute(
        """
        SELECT TOP (?) BreederID, KennelName, OwnerName, Website, Address, City, State, Email, Phone, Notes
        FROM sResults.Breeder
        WHERE (Notes LIKE 'Extrapolated from%' OR Notes LIKE 'Restored after%')
          AND (
                Website IS NULL OR Website = ''
             OR Address IS NULL OR Address = ''
             OR Email IS NULL OR Email = ''
             OR Phone IS NULL OR Phone = ''
          )
        ORDER BY BreederID DESC
        """,
        limit,
    )
    return cur.fetchall()


def main() -> None:
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    dropped = drop_bad_extrapolations(cur)
    print("dropped incomplete extrapolated breeders", dropped)
    conn.commit()
    junk = fix_junk_and_misnamed(cur)
    print("junk/misnamed", junk)
    titled = title_case_new_dogs(cur)
    print("title-cased", titled)
    missing = extrapolate_missing_kennels(cur)
    print("missing kennel prefixes", len(missing))
    for rec in missing[:60]:
        print(
            f"  dogs={rec['dogs']:4d} calls={rec['calls']:3d}  "
            f"{rec['kennel']!r}  owner={rec['owner']!r} ({rec['owner_n']})"
        )
    inserted = insert_missing_breeders(cur, missing)
    print("inserted breeders", inserted)
    collapsed = collapse_dogname_kennels(cur)
    print("collapsed dog-name kennels", collapsed)
    owners_filled = fill_missing_owners(cur)
    print("owners filled/fixed", owners_filled)
    conn.commit()
    need = breeders_needing_contact(cur, 40)
    print("need contact search", len(need))
    for r in need[:25]:
        print(f"  {r[0]} {r[1]!r} owner={r[2]!r}")
    conn.close()
    out = __import__("pathlib").Path(__file__).parent / "jrtcabreeders.com" / "missing_kennels.txt"
    out.write_text(
        "\n".join(
            f"{r['dogs']}\t{r['calls']}\t{r['kennel']}\t{r.get('owner') or ''}\t{r.get('breeder_id') or ''}"
            for r in missing
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
