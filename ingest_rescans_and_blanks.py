#!/usr/bin/env python3
"""Ingest pg*.pdf rescans + user-confirmed blanks; rewrite missing list."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from yearbook_vol_collective_audit import (
    KNOWN_UNNUMBERED,
    OUT_CONF,
    UPDATED,
    load_baseline,
    page_num_from_filename,
    pdfs_in,
    save_baseline,
    write_confidence_csv,
)
from yearbook_vol_trust_pass import (
    OUT_TXT,
    gaps_missing,
    pages_by_grade,
    printed_cap,
    trust_merge,
    vol_folders,
)

OUT_SPLIT = Path(
    r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
) / "_yearbook_vol_trust_missing_split.txt"
OUT_SUM = Path(
    r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
) / "_yearbook_vol_trust_summary.csv"


def main() -> int:
    baseline = load_baseline()
    ingested: dict[str, list[tuple[int, str]]] = {}

    for folder in vol_folders():
        name = folder.name
        cap = printed_cap(folder)
        got: list[tuple[int, str]] = []

        # 1) blanks / section = structural S
        for n in sorted(KNOWN_UNNUMBERED.get(name, set())):
            if 1 <= n <= cap:
                trust_merge(
                    baseline,
                    name,
                    n,
                    {
                        "confidence": 100,
                        "grade": "S",
                        "reason": "blank/unnumbered leaf (user-confirmed or known)",
                        "source": "structural",
                        "pdf": "",
                        "pdf_page": "",
                    },
                )

        # 2) filename-named rescan PDFs
        for pdf in pdfs_in(folder):
            nums = page_num_from_filename(pdf)
            if not nums:
                continue
            for i, n in enumerate(nums):
                if not (1 <= n <= max(cap, 400)):
                    continue
                trust_merge(
                    baseline,
                    name,
                    n,
                    {
                        "confidence": 92,
                        "grade": "A",
                        "reason": f"rescan filename {pdf.name}",
                        "source": "filename_rescan",
                        "pdf": pdf.name,
                        "pdf_page": str(i + 1),
                    },
                )
                got.append((n, pdf.name))
        ingested[name] = sorted(set(got), key=lambda x: x[0])

    save_baseline(baseline)
    write_confidence_csv(baseline)

    lines = [
        "AFTER RESCANS + BLANKS — missing page numbers",
        "=============================================",
        "Blanks (user-confirmed) counted present (grade S).",
        "pg*.pdf rescans counted present (grade A from filename).",
        "",
    ]
    summaries = []
    print("MISSING AFTER RESCANS + BLANKS")
    print("==============================")
    for folder in vol_folders():
        name = folder.name
        cap = printed_cap(folder)
        known = KNOWN_UNNUMBERED.get(name, set())
        trusted, locked_d, weak_c = pages_by_grade(baseline, name, cap)
        present = trusted | locked_d
        # structural blanks already in trusted via S
        missing = gaps_missing(present, cap, known)
        # anything still only C
        uncertain = sorted(n for n in weak_c if n not in present)
        high = [n for n in missing if n not in set(uncertain)]

        print(f"{name}")
        print(
            f"  ingested rescans: "
            + (
                ",".join(str(n) for n, _ in ingested.get(name, []))
                if ingested.get(name)
                else "(none)"
            )
        )
        print(f"  blanks/S: {sorted(known) if known else '(none)'}")
        print(
            f"  HIGH-CONF missing ({len(high)}): "
            + (",".join(map(str, high)) if high else "(none)")
        )
        if uncertain:
            print(
                f"  UNCERTAIN_C remaining ({len(uncertain)}): "
                + ",".join(map(str, uncertain))
            )
        print()

        lines.append(name)
        lines.append(
            f"  ingested: "
            + (
                ",".join(str(n) for n, _ in ingested.get(name, []))
                if ingested.get(name)
                else "(none)"
            )
        )
        lines.append(
            f"  blanks: "
            + (",".join(map(str, sorted(known))) if known else "(none)")
        )
        lines.append(
            f"  HIGH-CONF missing ({len(high)}): "
            + (",".join(map(str, high)) if high else "(none)")
        )
        lines.append(
            f"  UNCERTAIN_C ({len(uncertain)}): "
            + (",".join(map(str, uncertain)) if uncertain else "(none)")
        )
        lines.append("")

        summaries.append(
            {
                "Folder": name,
                "PrintedCap": cap,
                "PresentCount": len(present),
                "MissingCount": len(high),
                "Missing": ",".join(map(str, high)),
                "UncertainC": ",".join(map(str, uncertain)),
                "Blanks": ",".join(map(str, sorted(known))),
                "IngestedRescans": ",".join(
                    str(n) for n, _ in ingested.get(name, [])
                ),
            }
        )

    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_SPLIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with OUT_SUM.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Folder",
                "PrintedCap",
                "PresentCount",
                "MissingCount",
                "Missing",
                "UncertainC",
                "Blanks",
                "IngestedRescans",
            ],
        )
        w.writeheader()
        w.writerows(summaries)
    print(f"Wrote {OUT_TXT}")
    print(f"Wrote {OUT_CONF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
