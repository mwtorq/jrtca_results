#!/usr/bin/env python3
"""Train yearbook font-matched Tesseract langs: jrtca_mono + jrtca_helv.

Renders synthetic yearbook lines via text2image (Courier New / Arial), builds
.lstmf, LSTM fine-tunes from eng.traineddata → tessdata_yearbook/*.traineddata
"""
from __future__ import annotations

import argparse
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

from yearbook_ocr_fonts import GROUP_FONTS, GROUP_LANG, TESSDATA_DIR, sync_runtime_tessdata

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
# lstmtraining fails to deserialize .lstmf under paths with spaces (OneDrive - …).
TRAIN_ROOT = Path(r"C:\Users\mw\AppData\Local\jrtca_font_train")
TESS = Path(r"C:\Program Files\Tesseract-OCR")
# Stock Windows eng is integer/fast — cannot fine-tune. Use tessdata_best float eng.
BEST_DIR = TRAIN_ROOT / "tessdata_best"
ENG = BEST_DIR / "eng.traineddata"
ENG_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata"
TEXT2IMAGE = TESS / "text2image.exe"
COMBINE = TESS / "combine_tessdata.exe"
LSTMTRAIN = TESS / "lstmtraining.exe"
TESSERACT = TESS / "tesseract.exe"


def ensure_best_eng() -> Path:
    """Float eng + stock configs (lstm.train) under BEST_DIR for TESSDATA_PREFIX."""
    BEST_DIR.mkdir(parents=True, exist_ok=True)
    # Without configs/, tesseract can't open "lstm.train" and writes OCR .txt instead of .lstmf
    cfg_src = TESS / "tessdata" / "configs"
    cfg_dst = BEST_DIR / "configs"
    if cfg_src.is_dir():
        cfg_dst.mkdir(exist_ok=True)
        for name in ("lstm.train", "lstmbox", "lstmdebug"):
            src = cfg_src / name
            if src.is_file():
                shutil.copy2(src, cfg_dst / name)
    if ENG.is_file() and ENG.stat().st_size > 1_000_000:
        return ENG
    print(f"Downloading tessdata_best eng → {ENG}", flush=True)
    import urllib.request

    urllib.request.urlretrieve(ENG_URL, ENG)
    return ENG

DOGS = [
    "Foxwarren Floyd",
    "Cottonwood Kitty",
    "Briarpatch Jake",
    "Windy Hill Sugarbaker",
    "Prestwick's Comet",
    "Three Oaks Stymie",
    "Lickity Split Vanna",
    "Farmcliff Kermit",
    "Button Top Solo",
    "Heaven Hill Jezebel",
    "Rustler's Camilla Moon",
    "Seaview Sonnet",
    "I Am Prancer",
    "Northwood Only",
    "KaCee Razz",
    "Eastlake Chasen",
    "Redwood Rumble",
    "Golden Hills Rush",
    "Fox Run Trek",
    "Bonnie Doon",
    "Lands End Nutmeg",
    "Blackland Shane",
    "Clearfork Rapid",
    "Undercover Missy",
]
OWNERS = [
    "John & Barbara Lowery",
    "Natalie Spalding",
    "Jack & Terri Batzer",
    "Debra Ellis",
    "Pat Cunningham",
    "Judy Petty",
    "Didi Gough",
    "Bob & Genie Franklin",
    "Michelle Davies",
    "Sandi Myers",
    "Tony & Lina Marchlinski",
    "Steve Clark",
    "Diana DeCant",
    "Florence Clark",
    "Emily Hempel",
    "Phillip & Lori Aaron",
    "Lloyd & Shirley Cox",
    "Lynn May Measles",
    "Chris & Angela Tremie",
    "Tom & Lucy Bevis",
]
CLASSES = [
    "Dog Pups, 4 up to 6 months, smooth",
    "Bitch Pups, 9 up to 12 months, r/br",
    "Bitches 1 yr & over, 12 1/2-15\", smooth",
    "Dogs, 1 yr & older, 10 up to 12 1/2\", smooth",
    "JRTCA Working Terrier Bitch, 12 1/2-15\"",
    "Pair Class",
    "Family Class",
    "California Bred",
    "Puppy Championship",
    "Championship Certificate (10-12 1/2\")",
    "Child Handler",
    "Junior Handler",
    "Open Adults",
    "ADULTS",
]
PLACES = ["1st", "2nd", "3rd", "4th", "5th", "6th", "Champion", "Reserve", "Best"]


def _training_lines(n: int, rng: random.Random) -> list[str]:
    lines: list[str] = []
    for _ in range(n):
        kind = rng.random()
        if kind < 0.22:
            lines.append(f"{rng.choice(CLASSES)}          Entries: {rng.randint(1, 28)}")
        elif kind < 0.3:
            lines.append("PUPPY CHAMPION & RESERVE")
        else:
            place = rng.choice(PLACES)
            lines.append(
                f"{place}: {rng.choice(DOGS)}, owned by {rng.choice(OWNERS)}"
            )
    lines.extend(
        [
            "1st: Windy Hill Sugarbaker, owned by Debra Ellis",
            "4th: I Am Prancer, owned by Diana DeCant",
            "Pair Class – Entries: 4",
            "10-12 1/2\" Champion: Lands End Nutmeg, owned by Emily Hempel",
            "10-12 1/2\" Reserve: Clearfork Rapid, owned by Phillip & Lori Aaron",
            "12 1/2-15\" Champion: Blackland Shane, owned by Lloyd & Shirley Cox",
            "12 1/2-15\" Reserve: Undercover Missy, owned by Lynn May Measles",
            "Bitches 1 yr & over, 12 1/2-15\", smooth         Entries: 9",
        ]
    )
    rng.shuffle(lines)
    return lines


def _run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        sys.stderr.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")
        raise RuntimeError(f"failed ({r.returncode}): {cmd[0]}")
    if (r.stderr or "").strip():
        # text2image logs to stderr on success
        tail = (r.stderr or "").strip().splitlines()[-3:]
        print("\n".join(tail), flush=True)
    return r


def build_lstmf(group: str, *, lines_per_font: int, seed: int) -> Path:
    lang = GROUP_LANG[group]
    work = TRAIN_ROOT / lang
    pages = work / "pages"
    if pages.exists():
        shutil.rmtree(pages)
    pages.mkdir(parents=True)
    fc_tmp = work / "fontconfig"
    fc_tmp.mkdir(exist_ok=True)

    rng = random.Random(seed)
    lines = _training_lines(lines_per_font, rng)
    # text2image wants plain text; avoid fancy dashes
    clean = [re.sub(r"[–—]", "-", ln) for ln in lines]
    text_file = work / "training_text.txt"
    text_file.write_text("\n".join(clean) + "\n", encoding="utf-8")

    ensure_best_eng()
    env = os.environ.copy()
    # lstmf must be built with the same float eng used for fine-tune
    env["TESSDATA_PREFIX"] = str(BEST_DIR)
    lstmf_paths: list[str] = []
    # Large multipage .lstmf often fail "Deserialize header" on Windows; keep chunks small.
    chunk_size = 40

    for _font_path, font_name in GROUP_FONTS[group]:
        safe = font_name.replace(" ", "_")
        for ci in range(0, len(clean), chunk_size):
            chunk = clean[ci : ci + chunk_size]
            chunk_txt = pages / f"{lang}_{safe}_{ci:04d}.txt"
            chunk_txt.write_text("\n".join(chunk) + "\n", encoding="utf-8")
            out_base = pages / f"{lang}_{safe}_{ci:04d}"
            _run(
                [
                    str(TEXT2IMAGE),
                    f"--text={chunk_txt}",
                    f"--outputbase={out_base}",
                    f"--font={font_name}",
                    "--fonts_dir=C:\\Windows\\Fonts",
                    f"--fontconfig_tmpdir={fc_tmp}",
                    "--ptsize=12",
                    "--resolution=300",
                    "--margin=40",
                    "--leading=32",
                    "--xsize=3600",
                    "--ysize=4800",
                    "--max_pages=1",
                    "--degrade_image=true",
                    "--rotate_image=false",
                    "--invert=false",
                    "--white_noise=true",
                    "--smooth_noise=true",
                    "--blur=true",
                ],
                env=env,
            )
            tif = out_base.with_suffix(".tif")
            if not tif.is_file():
                alts = sorted(pages.glob(f"{out_base.name}*.tif"))
                if not alts:
                    print(f"  WARN no tif for {out_base.name}", flush=True)
                    continue
                tif = alts[0]
            stem = tif.with_suffix("")
            _run(
                [
                    str(TESSERACT),
                    str(tif),
                    str(stem),
                    "-l",
                    "eng",
                    "--psm",
                    "6",
                    "--oem",
                    "1",
                    "lstm.train",
                ],
                env=env,
            )
            lstmf = Path(str(stem) + ".lstmf")
            if lstmf.is_file():
                lstmf_paths.append(str(lstmf.resolve()))
                print(f"  lstmf {lstmf.name}", flush=True)
            else:
                print(f"  WARN no lstmf for {tif.name}", flush=True)

    list_path = work / "list.train"
    # lstmtraining is picky: LF-only, no BOM; absolute paths OK if no spaces
    list_path.write_bytes(("\n".join(lstmf_paths) + "\n").encode("ascii"))
    print(f"{lang}: {len(lstmf_paths)} lstmf → {list_path}", flush=True)
    if len(lstmf_paths) < 2:
        raise RuntimeError(f"too few lstmf for {lang}")
    return list_path


def fine_tune(group: str, list_path: Path, *, max_iterations: int) -> Path:
    lang = GROUP_LANG[group]
    work = TRAIN_ROOT / lang
    eng_copy = work / "eng.traineddata"
    shutil.copy2(ENG, eng_copy)
    # Extract LSTM net (must be a known tessdata suffix, e.g. eng.lstm — not "eng.")
    start_lstm = work / "eng.lstm"
    if start_lstm.is_file():
        start_lstm.unlink()
    _run([str(COMBINE), "-e", str(eng_copy), str(start_lstm)])
    if not start_lstm.is_file():
        raise RuntimeError("eng.lstm missing after combine_tessdata -e")

    model_prefix = work / lang
    # lstmtraining auto-resumes leftover checkpoints and then fails to load fresh .lstmf
    for stale in work.glob(f"{lang}*"):
        if stale.suffix in {".checkpoint", ""} or stale.name.endswith("_checkpoint"):
            try:
                stale.unlink()
            except OSError:
                pass
    for stale in work.glob(f"{lang}_*.checkpoint"):
        stale.unlink(missing_ok=True)
    ckpt_file = work / f"{lang}_checkpoint"
    if ckpt_file.is_file():
        ckpt_file.unlink()
    _run(
        [
            str(LSTMTRAIN),
            "--model_output",
            str(model_prefix),
            "--continue_from",
            str(start_lstm),
            "--traineddata",
            str(eng_copy),
            "--train_listfile",
            str(list_path),
            "--max_iterations",
            str(max_iterations),
            "--target_error_rate",
            "0.5",
            "--learning_rate",
            "0.0001",
        ]
    )
    ckpts = sorted(work.glob("*checkpoint"), key=lambda p: p.stat().st_mtime)
    if not ckpts:
        raise RuntimeError(f"no checkpoint for {lang}")
    ckpt = ckpts[-1]
    print(f"checkpoint {ckpt.name}", flush=True)

    TESSDATA_DIR.mkdir(parents=True, exist_ok=True)
    out_td = TESSDATA_DIR / f"{lang}.traineddata"
    _run(
        [
            str(LSTMTRAIN),
            "--stop_training",
            "--continue_from",
            str(ckpt),
            "--traineddata",
            str(eng_copy),
            "--model_output",
            str(out_td),
        ]
    )
    print(f"WROTE {out_td} ({out_td.stat().st_size} bytes)", flush=True)
    sync_runtime_tessdata()
    return out_td


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--group",
        choices=["mono_typewriter", "helvetica_yearbook", "all"],
        default="all",
    )
    ap.add_argument("--lines", type=int, default=500)
    ap.add_argument("--iterations", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()

    try:
        ensure_best_eng()
    except Exception as e:
        print(f"failed to get tessdata_best eng: {e}", file=sys.stderr)
        return 1

    groups = (
        ["mono_typewriter", "helvetica_yearbook"]
        if args.group == "all"
        else [args.group]
    )
    for g in groups:
        print(f"==== {g} / {GROUP_LANG[g]} ====", flush=True)
        lst = build_lstmf(g, lines_per_font=args.lines, seed=args.seed)
        if not args.skip_train:
            fine_tune(g, lst, max_iterations=args.iterations)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
