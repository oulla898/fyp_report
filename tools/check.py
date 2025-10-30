import re, glob, os, sys

# 1) Collect all \cite keys from .tex files
cite_pat = re.compile(r'\\cite[t|p|author|year|alt|]{0,6}\s*\{([^}]+)\}')
tex_files = glob.glob('**/*.tex', recursive=True)
cited = set()
for path in tex_files:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for m in cite_pat.finditer(f.read()):
            for k in m.group(1).split(','):
                cited.add(k.strip())

# 2) Collect all @...{key, from .bib
bib_files = glob.glob('references/*.bib')
bibkeys = set()
key_pat = re.compile(r'@\w+\{([^,]+),')
for path in bib_files:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for m in key_pat.finditer(f.read()):
            bibkeys.add(m.group(1).strip())

missing_in_bib = sorted(cited - bibkeys)
unused_in_bib = sorted(bibkeys - cited)

print('Missing in .bib:', missing_in_bib or 'None')
print('Unused in .bib:', unused_in_bib or 'None')

# 3) Basic spelling sanity: warn on uppercase/lowercase variations
mixed = sorted({k for k in cited for j in cited if k.lower()==j.lower() and k!=j})
print('Case-variant duplicate cite keys:', mixed or 'None')

# Exit non-zero if there are problems
sys.exit(1 if missing_in_bib else 0)