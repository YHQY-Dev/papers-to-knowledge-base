# Static HTML knowledge site (no npm for readers)

## Goals

- Double-click or any static host works
- Textbook chapters + glossary with bidirectional links
- Math via KaTeX CDN
- Citations = DOI / OA only

## Minimal file set

```text
{DOMAIN}-web/
  index.html
  assets/style.css
  assets/site.js
  chapters/ch00.html …
  terms/{slug}.html
  symbols.html
  references.html
  about.html
```

## Shared head snippet

```html
<link rel="stylesheet" href="../assets/style.css" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[
    {left:'$$',right:'$$',display:true},
    {left:'$',right:'$',display:false}]});"></script>
```

Adjust relative paths (`../` vs `./`) per folder depth.

## Glossary pattern

- Maintain a controlled list of term `id`s (JSON or a generated `terms/index.html`).
- In chapters, link explicitly: `<a class="term" href="../terms/scattering-vector.html">…</a>`.
- Each term page lists backlinks to chapters (generate when building HTML, or maintain by hand for small sites).
- Do **not** auto-link arbitrary words.

## Layout CSS essentials

```css
:root { --prose: min(64rem, 100%); --max: min(88rem, 100%); }
main { max-width: var(--max); margin: 0 auto; padding: 2rem clamp(1.25rem, 4vw, 2.5rem); }
.prose { max-width: var(--prose); width: 100%; margin-inline: auto; }
.prose table { width: 100%; border-collapse: collapse; }
.prose th, .prose td { padding: 1rem 1.4rem; border: 1px solid #ddd; vertical-align: top; }
```

Prefer local/system fonts over Google Fonts when latency matters.

## Math / units

- Prefer `$...$` / `$$...$$`
- Write angstrom as the character `Å` inside math
- Never leave `\unicode{...}` visible in the page

## Optional bilingual

- Duplicate trees `zh/` and `en/`, or `*.zh.html` / `*.en.html`
- Language switch jumps to the sibling page; if missing, show “coming soon” + link to primary language

## Generation options

| Approach | When |
|----------|------|
| Hand-authored HTML | Small sites, max control |
| MD/MDX → HTML script | Larger curricula; still commit/emit plain HTML |
| Astro/etc. build | Only if user wants; deliver `dist/` as the artifact |

Readers must not be told to run `npm install` to read the site.
