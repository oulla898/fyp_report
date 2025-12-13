# Visual Abstract Generation

Professional academic visual generator for the Smart Healthcare Robot project.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set your Gemini API key:
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key-here"

# Or add to your environment variables permanently
```

3. Generate visual abstract:
```bash
npm run generate:visual-abstract
```

## Output

The generated visual abstract will be saved in `figures/visual-abstract-[timestamp].png`

## Design Specifications

- **Format:** 16:9 (1920x1080px)
- **Style:** Minimalist academic, white background
- **Colors:** Navy blue, teal, gold accents
- **Content:** Robot illustration, system architecture, benefits

The visual is designed to be publication-ready for academic journals and conference presentations.
