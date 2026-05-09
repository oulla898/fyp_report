"""
compare_pdfs.py
Compares the LaTeX-compiled main.pdf with the manually-edited submitted PDF.
Outputs text diffs and extracted images side-by-side for review.
"""

import os
import sys
import hashlib
import difflib
import re
from pathlib import Path

try:
    import pypdf
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf not installed. Run: pip install pypdf")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = Path(r"C:\Users\oulla\Desktop\SQU\competetions\sumo robot\fyp\report")
LATEX_PDF   = BASE / "main.pdf"                          # compiled from LaTeX
SUBMIT_PDF  = BASE / "FYP PROJECT REPORT_submited.pdf"  # manually edited

OUT_DIR = Path(__file__).parent / "pdf_diff_output"
IMG_DIR = OUT_DIR / "images"
OUT_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

REPORT_FILE = OUT_DIR / "diff_report.txt"


# ── Helpers ────────────────────────────────────────────────────────────────────

def clean_text(raw: str) -> str:
    """Normalise extracted PDF text so trivial whitespace differences are ignored."""
    raw = re.sub(r'\s+', ' ', raw)   # collapse whitespace
    raw = raw.strip()
    # normalise common ligatures / encoding artefacts
    raw = raw.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    raw = raw.replace('’', "'").replace('‘', "'")
    raw = raw.replace('“', '"').replace('”', '"')
    raw = raw.replace('–', '-').replace('—', '--')
    return raw


def extract_text_by_page(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(clean_text(text))
    return pages


def extract_images_by_page(path: Path, prefix: str, out_dir: Path) -> dict[int, list[Path]]:
    """
    Extracts all images from each page. Returns {page_number: [saved_paths]}.
    Skips images that cannot be decoded gracefully.
    """
    reader = PdfReader(str(path))
    result: dict[int, list[Path]] = {}

    for page_num, page in enumerate(reader.pages, start=1):
        saved: list[Path] = []
        try:
            resources = page.get("/Resources")
            if resources is None:
                result[page_num] = saved
                continue
            xobject = resources.get("/XObject")
            if xobject is None:
                result[page_num] = saved
                continue

            if hasattr(xobject, "get_object"):
                xobject = xobject.get_object()

            idx = 0
            for name in xobject:
                obj = xobject[name]
                if hasattr(obj, "get_object"):
                    obj = obj.get_object()
                subtype = obj.get("/Subtype")
                if subtype != "/Image":
                    continue

                # Determine extension from filter
                filters = obj.get("/Filter", "")
                if isinstance(filters, list):
                    filters = filters[-1]
                filters = str(filters)

                if "DCT" in filters:
                    ext = "jpg"
                elif "PNG" in filters or "Flate" in filters:
                    ext = "png"
                elif "JBIG2" in filters:
                    ext = "jbig2"
                else:
                    ext = "bin"

                try:
                    data = obj.get_data()
                except Exception:
                    continue

                if len(data) < 100:   # skip tiny/blank images
                    continue

                fname = out_dir / f"{prefix}_p{page_num:03d}_{idx:02d}.{ext}"
                fname.write_bytes(data)
                saved.append(fname)
                idx += 1
        except Exception as e:
            pass  # best-effort per page

        result[page_num] = saved

    return result


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def image_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# ── Main comparison ────────────────────────────────────────────────────────────

def main():
    print(f"LaTeX PDF  : {LATEX_PDF}")
    print(f"Submitted  : {SUBMIT_PDF}")
    print()

    if not LATEX_PDF.exists():
        sys.exit(f"ERROR: cannot find {LATEX_PDF}")
    if not SUBMIT_PDF.exists():
        sys.exit(f"ERROR: cannot find {SUBMIT_PDF}")

    # ── Text comparison ────────────────────────────────────────────────────────
    print("Extracting text …")
    latex_pages  = extract_text_by_page(LATEX_PDF)
    submit_pages = extract_text_by_page(SUBMIT_PDF)

    n_latex  = len(latex_pages)
    n_submit = len(submit_pages)

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("FYP REPORT PDF DIFF  (LaTeX main.pdf  vs  submitted PDF)")
    lines.append("=" * 72)
    lines.append(f"LaTeX PDF page count  : {n_latex}")
    lines.append(f"Submitted PDF pages   : {n_submit}")
    lines.append("")

    if n_latex != n_submit:
        lines.append(f"*** PAGE COUNT DIFFERS: {n_latex} vs {n_submit} ***")
        lines.append("")

    text_diff_count = 0
    max_pages = max(n_latex, n_submit)

    for i in range(max_pages):
        a = latex_pages[i]  if i < n_latex  else "<MISSING PAGE>"
        b = submit_pages[i] if i < n_submit else "<MISSING PAGE>"

        if a == b:
            continue

        # Word-level diff
        a_words = a.split()
        b_words = b.split()

        if a_words == b_words:
            continue  # only whitespace differs after normalisation

        text_diff_count += 1
        page_label = f"PAGE {i+1}"
        lines.append("-" * 72)
        lines.append(f"TEXT DIFFERENCE on {page_label}")
        lines.append("-" * 72)

        # Unified diff on sentences (split by period/newline for readability)
        a_sents = re.split(r'(?<=[.!?])\s+', a)
        b_sents = re.split(r'(?<=[.!?])\s+', b)

        diff = difflib.unified_diff(
            a_sents, b_sents,
            fromfile=f"main.pdf  p{i+1}",
            tofile=f"submitted p{i+1}",
            lineterm=""
        )
        diff_lines = list(diff)
        if diff_lines:
            lines.extend(diff_lines)
        else:
            # Fall back to character-level diff snippet
            matcher = difflib.SequenceMatcher(None, a, b)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != 'equal':
                    lines.append(f"  [{tag}]")
                    lines.append(f"    LATEX   : {repr(a[max(0,i1-40):i2+40])}")
                    lines.append(f"    SUBMIT  : {repr(b[max(0,j1-40):j2+40])}")
        lines.append("")

    if text_diff_count == 0:
        lines.append("No text differences detected after normalisation.")
    else:
        lines.append(f"Total pages with text differences: {text_diff_count}")

    lines.append("")

    # ── Image comparison ───────────────────────────────────────────────────────
    print("Extracting images …")
    latex_imgs  = extract_images_by_page(LATEX_PDF,  "latex",  IMG_DIR)
    submit_imgs = extract_images_by_page(SUBMIT_PDF, "submit", IMG_DIR)

    lines.append("=" * 72)
    lines.append("IMAGE COMPARISON")
    lines.append("=" * 72)

    img_diff_count = 0
    all_pages = sorted(set(latex_imgs) | set(submit_imgs))

    for page_num in all_pages:
        l_imgs = latex_imgs.get(page_num, [])
        s_imgs = submit_imgs.get(page_num, [])

        l_hashes = [md5(p) for p in l_imgs]
        s_hashes = [md5(p) for p in s_imgs]

        if l_hashes == s_hashes:
            continue

        img_diff_count += 1
        lines.append(f"\nPage {page_num}: image difference")
        lines.append(f"  LaTeX    images ({len(l_imgs)}): " +
                     ", ".join(p.name for p in l_imgs) if l_imgs else "  LaTeX    images: (none)")
        lines.append(f"  Submitted images ({len(s_imgs)}): " +
                     ", ".join(p.name for p in s_imgs) if s_imgs else "  Submitted images: (none)")

        # Match by position and report hash diffs
        for idx in range(max(len(l_imgs), len(s_imgs))):
            lh = l_hashes[idx] if idx < len(l_hashes) else "MISSING"
            sh = s_hashes[idx] if idx < len(s_hashes) else "MISSING"
            if lh != sh:
                lname = l_imgs[idx].name if idx < len(l_imgs) else "n/a"
                sname = s_imgs[idx].name if idx < len(s_imgs) else "n/a"
                lines.append(f"  Image {idx}: DIFFERENT")
                lines.append(f"    LaTeX   : {lname}  (md5={lh})")
                lines.append(f"    Submitted: {sname}  (md5={sh})")

    if img_diff_count == 0:
        lines.append("No image differences detected.")
    else:
        lines.append(f"\nTotal pages with image differences: {img_diff_count}")
        lines.append(f"Extracted images saved to: {IMG_DIR}")

    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF REPORT")
    lines.append("=" * 72)

    report_text = "\n".join(lines)
    REPORT_FILE.write_text(report_text, encoding="utf-8")

    print()
    sys.stdout.buffer.write((report_text + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    print()
    print(f"Report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
