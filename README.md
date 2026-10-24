# CV

LaTeX source for Benjamin Anderson's CV. The document is a single A4 page.

## Files

| Path | Purpose |
| --- | --- |
| `main.tex` | CV content: contact details, projects, experience, references, and education. |
| `developercv.cls` | Local LaTeX class: page layout, fonts, colours, section headings, and entry macros. |
| `BenjaminAnderson-CV.pdf` | Latest rendered CV. |
| `cv.md` | Generated terminal-friendly Markdown for engiebenji.com. |
| `scripts/latex_to_markdown.py` | Converts `main.tex` into `cv.md`. |
| `scripts/test_latex_to_markdown.py` | Tests for the converter. |
| `HANDOVER.md` | Integration brief for the engiebenji.com project. |
| `Resources/` | Archived copies of previously rendered CVs. |
| `main.pdf` | Older rendered copy, not used by the current build. |

## Requirements

TeX Live with pdfLaTeX and latexmk. On Arch Linux:

```bash
sudo pacman -S --needed texlive-basic texlive-latex texlive-latexrecommended \
  texlive-latexextra texlive-pictures texlive-fontsextra texlive-fontsrecommended \
  texlive-binextra
```

`texlive-fontsextra` provides the Raleway and FontAwesome packages. `texlive-fontsrecommended` provides the vector CM-Super typewriter font.

## Editing with VS Code

Install the [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) extension and open this directory as the VS Code workspace.

The repository includes `.vscode/settings.json`, which selects a `latexmk` + pdfLaTeX recipe that writes `BenjaminAnderson-CV.pdf`. Save `main.tex` to rebuild, or run **LaTeX Workshop: Build LaTeX project** from the command palette. Preview with **LaTeX Workshop: View LaTeX PDF**.

`main.tex` also contains `% !TEX program = pdflatex`, and `.latexmkrc` forces PDF mode. Do not use a LuaLaTeX or DVI recipe: this CV relies on pdfLaTeX-specific font setup, and `dvilualatex` fails while loading Raleway with `luaotfload`/`fontspec` errors.

## Editing content

Edit `main.tex` for all CV content. Leave the surrounding macros in place:

- `\cvsect{...}` creates a section heading.
- `\entry{date}{title}{organisation}{description}` creates an experience entry.
- `\QRentry{title}{description}{url}` creates a project entry with a QR code.
- `\halfentry{name}{role}{contact}` creates a reference entry.
- `\halfentrydate{date}{title}{institution}{details}` creates an education entry.

Text is written in LaTeX, so escape special characters such as `&`, `%`, `$`, `#`, and `_`. Use `\&` for an ampersand.

Edit `developercv.cls` only when changing layout or styling. The `lining` option on the `raleway` package keeps numbers in lining figures to match the original design.

## Website CV

`main.tex` remains the single source of truth. After changing the CV, regenerate the Markdown copy used by engiebenji.com:

```bash
python3 scripts/latex_to_markdown.py
python3 scripts/test_latex_to_markdown.py
python3 scripts/latex_to_markdown.py --check
```

The converter is CV-specific: it understands the macros in `main.tex` and
fails loudly on anything it does not recognise. It omits the phone number and
referee details from the public Markdown. Project links are rewritten to the
current website routes.

`cv.md` is generated and should not be edited by hand. See `HANDOVER.md` for
the website integration instructions and the exact terminal behaviour expected
at `/cv/`.

## Building the PDF

Run commands from this directory:

```bash
latexmk -pdf -jobname=BenjaminAnderson-CV main.tex
```

This writes `BenjaminAnderson-CV.pdf` and reruns LaTeX as many times as needed. To build to `main.pdf` instead:

```bash
latexmk -pdf main.tex
```

To force a full rebuild after changing fonts or the class file:

```bash
latexmk -g -pdf -jobname=BenjaminAnderson-CV main.tex
```

To remove auxiliary files while keeping the PDF:

```bash
latexmk -c -jobname=BenjaminAnderson-CV
```

## Checking the result

Confirm the PDF is one page and A4:

```bash
pdfinfo BenjaminAnderson-CV.pdf | grep -E 'Pages|Page size'
```

Warnings such as `Font shape U/fontawesome... undefined` are harmless; FontAwesome 4 substitutes its correct internal font shape. QR codes and hyperlinks may require multiple LaTeX passes, which `latexmk` handles automatically.

## Git

The rendered PDF and old build artefacts are tracked in the repository. After rebuilding, review the changes before committing:

```bash
git status
git diff --stat
```
