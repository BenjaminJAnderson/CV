# CV

LaTeX source for Benjamin Anderson's CV. The document is a single A4 page.

## Files

| Path | Purpose |
| --- | --- |
| `main.tex` | CV content: contact details, projects, experience, references, and education. |
| `developercv.cls` | Local LaTeX class: page layout, fonts, colours, section headings, and entry macros. |
| `BenjaminAnderson-CV.pdf` | Latest rendered CV. |
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

## Editing content

Edit `main.tex` for all CV content. Leave the surrounding macros in place:

- `\cvsect{...}` creates a section heading.
- `\entry{date}{title}{organisation}{description}` creates an experience entry.
- `\QRentry{title}{description}{url}` creates a project entry with a QR code.
- `\halfentry{name}{role}{contact}` creates a reference entry.
- `\halfentrydate{date}{title}{institution}{details}` creates an education entry.

Text is written in LaTeX, so escape special characters such as `&`, `%`, `$`, `#`, and `_`. Use `\&` for an ampersand.

Edit `developercv.cls` only when changing layout or styling. The `lining` option on the `raleway` package keeps numbers in lining figures to match the original design.

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
