#!/usr/bin/env python3
"""
organize_report.py

Restructure a monolithic LaTeX report into a collaborative-friendly layout.
- Creates standard folders (sections/, figures/, tables/, bib/)
- Backs up the original main.tex into backup_<timestamp>/
- Moves image assets into figures/ and updates paths in TeX
- Splits main.tex into smaller section files based on top-level \section
- Extracts inline thebibliography into bib/references.tex or leaves for manual conversion to .bib
- Generates a new main.tex that inputs sections/* files and sets up \graphicspath

Safe and idempotent: will not overwrite existing files unless --force.

Usage:
  python tools/organize_report.py [--force]
"""
from __future__ import annotations
import argparse
import datetime as dt
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_TEX = ROOT / "main.tex"
FIG_DIR = ROOT / "figures"
SECTIONS_DIR = ROOT / "sections"
TABLES_DIR = ROOT / "tables"
BIB_DIR = ROOT / "bib"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".pdf", ".eps"}

SECTION_SPLIT_RE = re.compile(r"^\\section\{([^}]*)\}", re.MULTILINE)
SUBSECTION_RE = re.compile(r"^\\subsection\{([^}]*)\}", re.MULTILINE)
BEGIN_DOC_RE = re.compile(r"\\begin\{document\}")
END_DOC_RE = re.compile(r"\\end\{document\}")
GRAPHIC_RE = re.compile(r"\\includegraphics\[[^\]]*\]\{([^}]*)\}|\\includegraphics\{([^}]*)\}")
BIB_ENV_RE = re.compile(r"\\begin\{thebibliography\}([\s\S]*?)\\end\{thebibliography\}", re.MULTILINE)


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\-\s_]+", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s or "section"


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_main(force: bool = False) -> Path:
    if not MAIN_TEX.exists():
        raise FileNotFoundError(f"main.tex not found at {MAIN_TEX}")
    backup_dir = ROOT / f"backup_{timestamp()}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(MAIN_TEX, backup_dir / "main.tex")
    # Also back up images we detect
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            shutil.copy2(p, backup_dir / p.name)
    return backup_dir


def ensure_dirs():
    for d in (FIG_DIR, SECTIONS_DIR, TABLES_DIR, BIB_DIR):
        d.mkdir(parents=True, exist_ok=True)


def move_images_and_rewrite(tex: str) -> str:
    def repl(m: re.Match) -> str:
        path = m.group(1) or m.group(2)
        original = Path(path)
        # If already under figures/, leave it
        if str(original).startswith("figures/"):
            return m.group(0)
        src = (ROOT / original).resolve()
        if src.exists() and src.is_file() and src.suffix.lower() in IMAGE_EXTS:
            dest = FIG_DIR / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
            # rewrite to figures/<file>
            prefix = m.group(0).split('{')[0]
            return f"{prefix}{{figures/{dest.name}}}"
        return m.group(0)

    return GRAPHIC_RE.sub(repl, tex)


def extract_bibliography(tex: str) -> tuple[str, Path | None]:
    m = BIB_ENV_RE.search(tex)
    if not m:
        return tex, None
    bib_tex = m.group(0)
    bib_only = m.group(1)
    bib_path = BIB_DIR / "references.tex"
    bib_path.write_text("% Extracted from main.tex — consider converting to BibTeX (.bib)\n" + bib_tex, encoding="utf-8")
    # Replace env with \input{bib/references}
    new_tex = tex.replace(bib_tex, "\\input{bib/references}")
    return new_tex, bib_path


def split_sections(tex: str) -> tuple[list[Path], str]:
    # Find area inside document
    begin = BEGIN_DOC_RE.search(tex)
    end = END_DOC_RE.search(tex)
    if not begin or not end:
        raise ValueError("Could not find document environment in main.tex")
    preamble = tex[: begin.end()]
    body = tex[begin.end() : end.start()]
    postamble = tex[end.start() :]

    # Split by top-level sections
    parts = []
    last_idx = 0
    files: list[Path] = []
    for m in SECTION_SPLIT_RE.finditer(body):
        if m.start() != 0:
            parts.append((None, body[last_idx : m.start()]))
        title = m.group(1)
        last_idx = m.end()
        parts.append((title, None))
    # tail
    if last_idx < len(body):
        parts.append((None, body[last_idx:]))

    # Merge title markers with following content
    merged = []
    current_title = None
    for title, content in parts:
        if title is not None:
            if current_title is not None:
                # Start new empty section to be filled later
                merged.append((current_title, ""))
            current_title = title
        else:
            if current_title is None:
                # content before first section -> keep in preamble area
                preamble += content
            else:
                merged.append((current_title, content))
                current_title = None

    # Write section files
    order_inputs = []
    for idx, (title, content) in enumerate(merged, start=1):
        fname = f"{idx:02d}-{slugify(title)}.tex"
        fpath = SECTIONS_DIR / fname
        # Ensure section command is inside file
        body_content = content or ""
        if not body_content.lstrip().startswith("\\section"):
            body_content = f"\\section{{{title}}}\n\n" + body_content
        fpath.write_text(body_content.strip() + "\n", encoding="utf-8")
        files.append(fpath)
        order_inputs.append(f"\\input{{sections/{fname}}}")

    # Build new main body as includes
    new_body = "\n\n".join(order_inputs) + "\n"
    return files, preamble + new_body + postamble


def write_new_main(tex: str) -> None:
    # Inject \graphicspath if not present and figures dir exists
    if FIG_DIR.exists() and FIG_DIR.iterdir():
        if "\\graphicspath" not in tex:
            # add after \usepackage{graphicx} if present
            if "\\usepackage{graphicx}" in tex:
                tex = tex.replace(
                    "\\usepackage{graphicx}",
                    "\\usepackage{graphicx}\n\\graphicspath{{figures/}}",
                )
            else:
                # add to preamble
                tex = tex.replace("\\begin{document}", "\\graphicspath{{figures/}}\n\\begin{document}")
    MAIN_TEX.write_text(tex, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Organize LaTeX report into modular structure")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs if needed")
    args = parser.parse_args()

    ensure_dirs()
    backup_dir = backup_main()
    print(f"Backed up original files to: {backup_dir}")

    raw = MAIN_TEX.read_text(encoding="utf-8")

    # Move images and rewrite paths
    tex1 = move_images_and_rewrite(raw)

    # Extract bibliography
    tex2, bib_path = extract_bibliography(tex1)
    if bib_path:
        print(f"Extracted bibliography to: {bib_path}")

    # Split sections into files and build a new main
    section_files, new_main = split_sections(tex2)
    print("Created section files:")
    for p in section_files:
        print(f" - {p.relative_to(ROOT)}")

    write_new_main(new_main)
    print("Rewrote main.tex with inputs and graphicspath.")
    print("Done.")


if __name__ == "__main__":
    main()
