import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS_DIR = ROOT / "sections"
MAIN_TEX = ROOT / "main.tex"
LEGACY_BIB_TEX = ROOT / "bib" / "references.tex"
BIB_DIR = ROOT / "references"
BIB_FILE = BIB_DIR / "references.bib"


def find_citation_keys() -> set[str]:
    tex_files = [MAIN_TEX] + sorted(SECTIONS_DIR.glob("*.tex"))
    cite_re = re.compile(r"\\cite\{([^}]+)\}")
    keys: set[str] = set()
    for tex in tex_files:
        if not tex.exists():
            continue
        content = tex.read_text(encoding="utf-8", errors="ignore")
        for m in cite_re.finditer(content):
            for k in m.group(1).split(","):
                k = k.strip()
                if k:
                    keys.add(k)
    return keys


def parse_legacy_bibliography() -> dict[str, str]:
    """Parse bib/references.tex (thebibliography) to a mapping key->raw entry string.

    We'll convert each entry into a simple @misc using the raw text in a 'note' field.
    """
    entries: dict[str, str] = {}
    if not LEGACY_BIB_TEX.exists():
        return entries
    text = LEGACY_BIB_TEX.read_text(encoding="utf-8", errors="ignore")
    # Remove any end markers that may leak into parsing
    text = text.replace("\\end{thebibliography}", "")
    # Split on \bibitem{key}
    parts = re.split(r"\\bibitem\{([^}]+)\}", text)
    # parts: [prefix, key1, entry1, key2, entry2, ...]
    for i in range(1, len(parts), 2):
        key = parts[i].strip()
        entry_raw = parts[i + 1].strip()
        # Collapse whitespace
        entry_clean = re.sub(r"\s+", " ", entry_raw)
        entries[key] = entry_clean
    return entries


def to_bib_entry_from_legacy(key: str, legacy_text: str) -> str:
    # Heuristic: try to extract a title between first period segments; fallback to full note
    title_match = re.search(r"\\textit\{([^}]+)\}", legacy_text)
    title = title_match.group(1) if title_match else None
    # Basic @misc entry
    fields = []
    if title:
        fields.append(f"  title = {{{title}}}")
    fields.append(f"  note = {{{legacy_text}}}")
    return "@misc{" + key + ",\n" + ",\n".join(fields) + "\n}\n\n"


def write_bib_file(keys: set[str], legacy_map: dict[str, str]) -> None:
    BIB_DIR.mkdir(parents=True, exist_ok=True)
    existing = BIB_FILE.read_text(encoding="utf-8", errors="ignore") if BIB_FILE.exists() else ""
    # Build a map of existing entries by key
    existing_map: dict[str, str] = {}
    for m in re.finditer(r"@\w+\{([^,]+),", existing):
        existing_map[m.group(1).strip()] = "present"

    out = []
    # Preserve existing content
    if existing:
        out.append(existing if existing.endswith("\n") else existing + "\n")

    added = 0
    for key in sorted(keys):
        if key in existing_map:
            continue
        legacy = legacy_map.get(key)
        if legacy:
            out.append(to_bib_entry_from_legacy(key, legacy))
            added += 1
    if added:
        BIB_FILE.write_text("".join(out), encoding="utf-8")


def ensure_main_uses_bibtex() -> None:
    content = MAIN_TEX.read_text(encoding="utf-8", errors="ignore")
    if "\\bibliography{" in content:
        return
    # Replace legacy input of thebibliography with bibtex commands
    content_new = re.sub(r"\\input\{bib/references\}",
                         "\\bibliographystyle{unsrt}\n\\bibliography{references/references}",
                         content)
    if content != content_new:
        MAIN_TEX.write_text(content_new, encoding="utf-8")


def main():
    keys = find_citation_keys()
    legacy = parse_legacy_bibliography()
    write_bib_file(keys, legacy)
    ensure_main_uses_bibtex()
    print(f"Processed {len(keys)} citation keys. BibTeX file: {BIB_FILE}")


if __name__ == "__main__":
    main()


