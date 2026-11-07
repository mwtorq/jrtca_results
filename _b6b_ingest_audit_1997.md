# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=4  PASS=0  WARN=4  FAIL=0
Year verdict: **WARN**  SQL-apply unlock: YES

## Intent
- Apply finalize/catalog cleanups to stored HQ text (backup `*.pre_b6b`).
- Re-OCR only if FAIL remains after cleanup — not as the default path.

## Policy
- FAIL (blocks apply): smash, placeholders, leftover height/place garble after cleanup
- WARN: class_header_gap / owner_tail_trunc / structure residuals (image recovery debt)
- `handled by` lines excluded from mangled_by / missing_owned_by

## Per volume

| Verdict | Cleaned | Fail | Warn | Catalog | File |
|---------|---------|------|------|---------|------|
| WARN | True | 0 | 35 | C1×25,S4/O×4,O6×3,C6×3 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 30 | C1×25,O6×3,S4/O×2 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| WARN | True | 0 | 44 | C1×25,O6×7,S4/O×6,C6×6 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 34 | C1×25,O6×3,S4/O×3,C6×3 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (WARN)
- `O6` / `owner_tail_trunc`: 2nd: Rustler's Emma Peel, owned by Tony & Lir
- `O6` / `owner_tail_trunc`: 5th: Camerton Hall Impshi, owned by Jack & Pz
- `O6` / `owner_tail_trunc`: 4th: THEY V MY WV VY IALIVIILIEW, WFWE TL HL ILC, = 1st: Farmcliff Monet, owned by Charles & Sally Hickey Tl: Eroclr lace stressed Bir BAA em
- `S4/O` / `missing_owned_by`: 2nd: Kingmont Harlaquin, owr 3d by Lynda Banducci
- `S4/O` / `missing_owned_by`: 2nd: Button, owner not provideditch Pups, 9 up to 12 months, r/br             Entries: 10
- `S4/O` / `missing_owned_by`: 2nd: Blackland Luckyog Pups, 9 up to 12 months, 12 1/2-15" Entries: 5
- `S4/O` / `missing_owned_by`: 1st: Buster, ownedby Tim & Wendy Griffith
- `C6` / `orphan_entry_count`: 26
- `C6` / `orphan_entry_count`: 23
- `C6` / `orphan_entry_count`: 1
- `C1` / `class_header_gap`: 1st: Dashaway Elly, owned by Suzanne Birdsall
- `C1` / `class_header_gap`: 1st: Fox Run Risk, owned by Linda Cowasjee

### `1997 Vol I pt 2_ocr_hqmax.txt` (WARN)
- `O6` / `owner_tail_trunc`: Reserve: Fox Run Dagger, owned by Sandra Ferber Sr
- `O6` / `owner_tail_trunc`: 1st: Al INA, Wo LESS Set UA Ser Used IL Xr d hing "wl ERT Ter'ell Ber 1 4 EDT Hr nd er A ad rel 3rd: Farmcliff Duke, owned by Kim Hunter Atl LI TO El =. TEE WY 
- `O6` / `owner_tail_trunc`: 1st: rr 3n — "TFTEIENENWSI WEVWI dm fp IW mr iul Hr w F< 1st: Farmcliff Monet, owned by Charles & Sally Hickey I 7nd: Earmetoasad Talli sumer Bar BAsvecmremd El
- `S4/O` / `missing_owned_by`: 1st: High Mountain Lucy, Karen Vernon
- `S4/O` / `missing_owned_by`: 2nd: , Courtney Bottington
- `C1` / `class_header_gap`: 1st: Farmoliff Ben, owned by Bob Franklin
- `C1` / `class_header_gap`: 1st: Lizzie, owned by Rick & Mary Thornton
- `C1` / `class_header_gap`: 1st: Famliff Ben, owned by Bob Frankin
- `C1` / `class_header_gap`: 1st: Hopdiggity Star, owned by Kevin Winn
- `C1` / `class_header_gap`: 1st: Ridgeview Bon Bon, owned by D. Gough & J. L. Gibson
- `C1` / `class_header_gap`: 1st: T.J. Farms Dare, owned by Georgia Fisher
- `C1` / `class_header_gap`: 1st: Seaview Soozi, owned by Didi Gough

### `1997 Vol II pt 1_ocr_hqmax.txt` (WARN)
- `O6` / `owner_tail_trunc`: 1st: Farmcliff Hutch, owned by Dave & Marti McMahon New: Trmrermom di EE Tame ls mviaeme mod Loos BA
- `O6` / `owner_tail_trunc`: 6th: 1 RE Is FAVAMILA VE AWWYLE TD AAT WET WHET TA A a] wll hry 7 KLINE I) 5th: Farmcliff Spencer, owned by Bob Franklin FS ile, vedo obe oe BEA, 2." ™ LT meee 
- `O6` / `owner_tail_trunc`: 6th: TET) JT Ww Wivwdy IW MIM VY IK fa LIILIIGa, I= 1st: Farmcliff Tackle, owned by Megan Johnson be Sd, "Tee be AA. TL PY
- `O6` / `owner_tail_trunc`: IVE I& /2 wlldiHPIVLEL T All VGH VIVE Y ICG, VIVIITU WY VAYIG JUILLTTIYO | 10-12 1/2"2" Reserve: Lickity Split Sassy, owned by Bob Franklin AN 1/7 APU HL vonnin
- `O6` / `owner_tail_trunc`: AUULI RAVING GAANMEIVN G REOERYL | 10-12 4" Champion: Lickity Split Sassy, owned by Bob Franklin AA £28 9780 Me ce cence . Foon a IEE T oo Lb lh vss cm mel Enns
- `S4/O` / `missing_owned_by`: 6th: Blue Barns Tracker, R. & D. Zampella
- `S4/O` / `missing_owned_by`: 1st: Katlin Cortenbach, handling Little Orbit of Cortenbach
- `S4/O` / `missing_owned_by`: 3rd: Kari Carlsen, handling Westgate Ruffian
- `S4/O` / `missing_owned_by`: 1st: Ali Mae Hop, handling Hopdiggity Checkers
- `S4/O` / `missing_owned_by`: 2nd: Pat Martin, handling Bar-C Abilene Rose
- `S4/O` / `missing_owned_by`: 2nd: Matisse, Ruth Evans
- `C6` / `orphan_entry_count`: 8

### `1997 Vol II pt 2_ocr_hqmax.txt` (WARN)
- `O6` / `owner_tail_trunc`: Best: Farmcliff Holland, owned by Doug & Sue Tack EBacrnrmin' RDhiitn Bare fhicbhladt Atsneemel Inne Thm eed mie ie "Fao ne on IT
- `O6` / `owner_tail_trunc`: 2nd: uke AWATLg VRVIIWG WY CYTE LollliGr lida l 2nd: Farmcliff Becky, owned by D.Sturtz/J McCoy Trad: Datmir Arai me omoemd snimos of
- `O6` / `owner_tail_trunc`: 3rd: Woods End Cloudy, owned by Bob Franklin es Atlve removviaimil Toddler ovime sedi om od Exe os Fc of
- `S4/O` / `missing_owned_by`: Champion: Blue Jeans, Donna Pierce
- `S4/O` / `missing_owned_by`: 5th: Button Top Jim Winston, Joel Pritchet
- `S4/O` / `missing_owned_by`: 6th: Showbizz Fizz, al Darlene Irvine
- `C6` / `orphan_entry_count`: 03
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 12
- `C1` / `class_header_gap`: 1st: Hopdiggity Star, owned by Kevin Winn
- `C1` / `class_header_gap`: 1st: Farmcliff Fred, owned by Mark & Janice Bjorkland--- column RIGHT
- `C1` / `class_header_gap`: 1st: Wild Child, owned by Samuel Hopewell
