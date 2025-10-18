# FYP Report (LaTeX)

Modular, collaboration-friendly structure for an 80+ page report.

## Structure

- `main.tex` — master file, includes sections and sets up packages
- `sections/` — each top-level section in its own file
- `figures/` — all images live here; `\graphicspath{ {figures/} }` is set
- `tables/` — large tables extracted here
- `bib/references.tex` — temporary extracted inline bibliography (consider converting to BibTeX)
- `tools/organize_report.py` — script to restructure a monolithic `main.tex`
- `backup_YYYYMMDD_HHMMSS/` — backups of pre-organized files

## One-time: organize current report

```
python tools/organize_report.py
```

This will:
- Backup `main.tex` and detected images
- Move images into `figures/` and rewrite their paths in LaTeX
- Split `main.tex` into `sections/*.tex` by top-level `\\section{}`
- Extract inline bibliography to `bib/references.tex` and replace with `\\input{bib/references}`
- Rewrite `main.tex` to `\\input{sections/...}` and add `\\graphicspath{...}`

## Collaboration workflow

- Edit only your assigned files in `sections/`
- Add new images to `figures/` and reference them directly by filename
- Avoid editing `main.tex` unless changing packages or document settings

## Git basics

```
# First time
git init
git remote add origin https://github.com/oulla898/fyp_report.git

# Work
git checkout -b feature/chapter-3
# edit files
git add -A
git commit -m "Write Chapter 3 methodology"

# Push
git push -u origin feature/chapter-3
```

Open a Pull Request on GitHub for review and merging.

## Recommended next steps

- Convert `bib/references.tex` to a proper `references.bib` and switch to BibTeX:
  - Add to preamble: `\\bibliographystyle{plain}`
  - At end: `\\bibliography{references}`
- Add a `Makefile` or use `latexmk` for builds
- Add `
```
.vscode/settings.json
```
  to share LaTeX Workshop settings
