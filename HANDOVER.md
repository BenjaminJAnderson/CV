# Website CV handover

This document is the brief for the AI working on
[engiebenji.com](https://engiebenji.com). The job is to publish the CV as a
terminal-native page at `/cv/` and keep the printable PDF available for
download.

The CV repository is the source of truth. Do not rewrite the CV content inside
the website repository.

## What you are given

| File | Purpose |
| --- | --- |
| `cv.md` | Generated, terminal-friendly Markdown version of the CV. |
| `BenjaminAnderson-CV.pdf` | Printable PDF CV. |
| `scripts/latex_to_markdown.py` | Regenerates `cv.md` from `main.tex`. |
| `main.tex` | Canonical CV source. Do not edit from the website project. |

`cv.md` was generated from `main.tex` at the time of this handover. The
generated file deliberately:

- omits the phone number;
- omits referee names, emails and phone numbers;
- replaces the PDF QR-code links with normal links to `/projects/cube/` and
  `/projects/orthodox/`;
- uses `##` for sections and `###` for entries;
- ends with `References available on request.`

## Decisions already made

1. `cv` and `resume` open the terminal CV page at `/cv/`.
2. `download cv` and `cv pdf` download
   `/cv/BenjaminAnderson-CV.pdf`.
3. `cv` is a directory in the terminal filesystem containing
   `BenjaminAnderson-CV.pdf`, so `cd cv`, `ls cv` and Tab completion work.
4. The web CV omits phone and referee details; the PDF keeps the phone number
   and the LaTeX source keeps references.
5. The page uses the existing `TerminalLayout`, `.term-prose`, `.term-facts`
   and terminal styling. Do not introduce a new design system.

## Website facts to respect

- Astro static build with `trailingSlash: "always"`; use `/cv/`.
- Terminal shell: `src/layouts/TerminalLayout.astro`.
- Markdown rendering pattern: `src/pages/projects/[...slug].astro`.
- Content collections: `src/content.config.ts`.
- Existing `/about/` page is a good example of a simple terminal page:
  `src/pages/about.astro`.
- Site constants: `src/data/site.ts`.
- Commands: `src/data/commands.ts` and `src/lib/commands.ts`.
- Filesystem: `src/lib/terminal-fs.ts`.
- Terminal output helpers: `src/scripts/terminal.ts`.
- Unit tests: `tests/unit/commands.test.ts`, `tests/unit/terminal-fs.test.ts`.

The PDF already exists at `public/cv/BenjaminAnderson-CV.pdf`, so a page route
at `/cv/` can coexist with the PDF file.

## Implementation checklist

### 1. Add the Markdown entry

Copy `cv.md` to `src/content/cv/cv.md` unchanged.

Register a `cv` collection in `src/content.config.ts`. The file has no
frontmatter, so either leave the collection schema undefined or use an empty
object schema:

```ts
const cv = defineCollection({
  loader: glob({
    base: "./src/content/cv",
    pattern: "**/*.{md,mdx}",
  }),
});

export const collections = { projects, cv };
```

If Astro requires a schema in the installed version, add a minimal frontmatter
block to `src/content/cv/cv.md` and a matching schema. Do not change the CV
body.

### 2. Add the page

Create `src/pages/cv/index.astro`:

```astro
---
import { getEntry, render } from "astro:content";
import { site } from "../../data/site";
import TerminalLayout from "../../layouts/TerminalLayout.astro";

const entry = await getEntry("cv", "cv");

if (!entry) {
  throw new Error("Missing CV content at src/content/cv/cv.md");
}

const { Content } = await render(entry);
---

<TerminalLayout
  title="CV"
  description="CV of Benjamin Anderson, electronic engineer."
  path="~/cv"
  command="cat cv.md"
>
  <div class="term-prose cv-doc">
    <Content />
  </div>

  <p class="term-line term-dim">
    <a href={site.cvPdf}>download pdf</a>
    <a href="/projects/">projects</a>
    <a href="/about/">about</a>
    <a href="/">home</a>
  </p>
</TerminalLayout>
```

After the generated-file comment, the Markdown starts with
`# Benjamin Anderson`, so do not add a second `<h1>CV</h1>` above it.

### 3. Style the document

Add a small block to `src/styles/global.css` near the existing `.term-prose`
rules. Reuse the existing terminal tokens and do not restyle the whole site.

Suggested minimum:

```css
.cv-doc h1 {
  margin: 0 0 0.25rem;
  color: var(--text);
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.cv-doc h1 + p {
  color: var(--text-dim);
}

.cv-doc h3 {
  margin-top: 1.4rem;
}

.cv-doc h3 + p {
  margin: -0.2rem 0 0.6rem;
  color: var(--text-dim);
}

.cv-doc ul {
  margin-top: 0.35rem;
}
```

Check the mobile layout at widths below `700px`; existing `.term-prose` rules
collapse lists and headings already.

### 4. Update site constants

In `src/data/site.ts`, make the page and PDF paths explicit:

```ts
cv: "/cv/",
cvPdf: "/cv/BenjaminAnderson-CV.pdf",
```

Update every consumer of `site.cv`:

- `src/pages/about.astro`: the CV link should point to `site.cv`.
- `src/scripts/terminal.ts`: `renderContact()` should link to `site.cvPdf` for
  the downloadable file, labelled `BenjaminAnderson-CV.pdf` or `CV PDF`.
- `src/scripts/terminal.ts`: `renderSections()` should show both the CV page
  and the PDF download.
- `src/layouts/TerminalLayout.astro`: pass both paths to
  `buildTerminalFileSystem`.

### 5. Update commands

In `src/data/commands.ts`:

- Change the existing `cv` command to navigate to `/cv/`, with description
  `View the CV in the terminal.` and aliases `resume`.
- Add a separate command:

```ts
{
  id: "download-cv",
  label: "Download CV",
  description: "Download the printable CV as a PDF.",
  group: "navigate",
  aliases: ["download cv", "cv pdf"],
  keywords: ["resume", "pdf", "download"],
  action: {
    type: "navigate",
    href: "/cv/BenjaminAnderson-CV.pdf",
  },
}
```

- Add `download-cv` to the Navigation section of `helpSections`, next to `cv`.

Do not add a new command action type. `navigate` is enough.

### 6. Update the terminal filesystem

In `src/lib/terminal-fs.ts`, change the CV entry from a file to a directory:

```ts
{
  name: "cv",
  route: cvPage,
  kind: "dir",
  description: cvDescription,
  children: [
    {
      name: "BenjaminAnderson-CV.pdf",
      route: cvPdf,
      kind: "file",
      description: "download the printable CV",
    },
  ],
}
```

Update `buildTerminalFileSystem`'s signature to accept both paths, for example:

```ts
buildTerminalFileSystem(projects, cvPage, cvPdf, cvDescription)
```

Then update the call in `src/layouts/TerminalLayout.astro`.

Expected terminal behaviour after the change:

| Input | Result |
| --- | --- |
| `cv` | Opens `/cv/`. |
| `resume` | Opens `/cv/`. |
| `download cv` | Downloads `/cv/BenjaminAnderson-CV.pdf`. |
| `cv pdf` | Downloads `/cv/BenjaminAnderson-CV.pdf`. |
| `cd cv` | Navigates to `/cv/`. |
| `ls cv` | Lists `BenjaminAnderson-CV.pdf`. |
| `ls` | Lists `about/`, `cv/`, `projects/`. |
| Tab after `cd c` | Completes to `cd cv/`. |

### 7. Copy the current PDF

Replace the stale PDF with the current one from the CV repository:

```bash
cp /path/to/CV/BenjaminAnderson-CV.pdf \
  /path/to/Website/public/cv/BenjaminAnderson-CV.pdf
```

Then verify:

```bash
sha256sum /path/to/CV/BenjaminAnderson-CV.pdf \
  /path/to/Website/public/cv/BenjaminAnderson-CV.pdf
```

The two hashes must match.

### 8. Update tests

Update `tests/unit/terminal-fs.test.ts`:

- root listing still contains `about`, `cv`, `projects`;
- `cv` is now a directory at `/cv/`;
- it contains `BenjaminAnderson-CV.pdf` at
  `/cv/BenjaminAnderson-CV.pdf`;
- `cd cv` resolves to the directory;
- `ls cv` resolves the PDF child.

Update `tests/unit/commands.test.ts`:

- `cv` resolves to `{ type: "navigate", href: "/cv/" }`;
- `download-cv` resolves to the PDF path;
- the exact `helpSections` expectation includes `download-cv`.

Add a simple check if useful that no referee email or phone number appears in
the rendered CV source.

### 9. Documentation

Update the website `README.md`:

- mention `/cv/` in the available commands;
- add a short "CV" section explaining that `src/content/cv/cv.md` is generated
  from the CV repository and must not be edited directly;
- note the PDF source path.

## Guardrails

- Do not edit `main.tex` from the website project.
- Do not make the website copy canonical. CV content changes go through
  `main.tex` and the converter, then are copied into the website.
- `src/scripts/terminal.ts` currently has uncommitted local changes in the
  website working tree. Inspect `git diff src/scripts/terminal.ts` before
  editing and preserve those changes.
- Do not change boot behaviour, themes, ASCII effects, cursor trails or the
  existing project pages.
- Do not publish referee contact details or the phone number on `/cv/`.
- Keep the existing `.term-prose` links and typography. No new font or colour
  scheme.

## Regenerating the CV

From the CV repository:

```bash
python3 scripts/latex_to_markdown.py
python3 scripts/test_latex_to_markdown.py
python3 scripts/latex_to_markdown.py --check
```

Then copy the regenerated `cv.md` into `src/content/cv/cv.md` and rebuild the
website.

If a project URL changes, update `PROJECT_URL_REWRITES` in
`scripts/latex_to_markdown.py`, regenerate, and copy again.

## Definition of done

- `/cv/` renders the generated Markdown in the terminal layout.
- The PDF downloads from `/cv/BenjaminAnderson-CV.pdf`.
- `cv`, `resume`, `download cv`, `cv pdf`, `cd cv`, `ls cv` and Tab completion
  all behave as described above.
- No phone number or referee details are present in the HTML CV.
- `npm run check`, `npm run format:check`, `npm run test` and `npm run build`
  all pass.
- The built site contains `dist/cv/index.html` and
  `dist/cv/BenjaminAnderson-CV.pdf`.
