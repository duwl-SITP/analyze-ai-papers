# PDF Figure And Table Extraction

Use this file only for the auxiliary visual-support branch of the skill. Read it when the user explicitly asks to extract figures or tables from a PDF, convert a paper PDF into markdown with local image files, preserve captions, preserve section hierarchy, or when visual artifacts are necessary to help explain architectures, modules, pipeline flow, qualitative examples, or key tables.

When this branch writes files to disk, treat the method-named artifact folder as the canonical workspace for the run. Keep all extracted markdown, `images/`, and other generated extraction artifacts inside that folder, and reuse the exact same canonical folder name across preparatory and final outputs.

## Goals

The extraction workflow should:

- extract figures and tables from PDFs
- save rendered crops into a local `images/` directory
- insert relative image links into markdown
- preserve figure and table captions
- preserve section hierarchy
- associate figures with nearby paragraphs when possible

Prefer rendered-page region cropping over raw embedded-image extraction. Research papers often mix raster images, vector drawings, formulas, and page-level composition; raw embedded-image extraction misses many of those cases.

This is not the default path for ordinary paper summarization. Normal reading, summarization, and method analysis should stay text-first unless visuals materially help the user.

## Recommended stack

- `PyMuPDF`: primary PDF parser and page renderer
- `pdfplumber`: primary born-digital table detector
- `PyMuPDF` page text/drawing analysis: refine table candidates, shrink over-large boxes, and preserve rendered-page cropping
- `MinerU`: optional but preferred text/layout backbone for scanned PDFs and complex academic layouts

## Routing

Choose the extraction path based on the source:

Before choosing a path, first confirm that extraction is actually needed. If the user only wants a summary or method explanation and the visual content is not central, do not run extraction.

### Born-digital academic or arXiv PDFs

- Default to `scripts/extract_pdf_figures.py` only after the visual branch has been justified.
- Let the script extract text blocks, detect captions, crop rendered page regions, write `images/`, and emit markdown.
- This path is usually good enough for standard two-column papers, multimodal papers, and arXiv PDFs with selectable text.

### Scanned PDFs or OCR-heavy layouts

- Prefer MinerU first to produce a markdown skeleton that already captures section hierarchy and OCR text.
- Then run `scripts/extract_pdf_figures.py --skeleton-markdown <mineru.md>`.
- The script keeps the MinerU section structure, inserts relative image links near matching caption text, and still uses rendered-page crops for figure/table images.

### Multimodal research papers

- Still prefer rendered-page region cropping.
- Multimodal papers often include composite figures, vector diagrams, screenshots, dense tables, and mixed typography; page-region crops preserve the rendered appearance better than raw embedded-image extraction.

## Script contract

Use `scripts/extract_pdf_figures.py` for the actual extraction work.

Inputs:

- `--pdf <path>`: source PDF
- `--out-dir <path>`: parent output directory under which the script creates one method-named artifact folder
- `--method-name <name>`: optional method or model name used as the final artifact-folder name without lowercasing or slugification; if omitted, fall back to the PDF filename stem
- `--markdown-name <name>`: output markdown filename only, default `paper.md`; path components are not allowed
- `--skeleton-markdown <path>`: optional markdown skeleton, usually from MinerU
- `--force-regenerate`: remove previously generated extraction outputs for this method folder before writing new ones

Outputs under `<out-dir>/<method-folder>`:

- `<markdown-name>`: markdown with inserted relative image links
- `images/`: extracted figure/table crops

The method folder is the single landing place for intermediate extraction artifacts and final extraction outputs. If the user asks to regenerate, rerun extraction from the source PDF and do not reuse previously generated markdown or images as inputs. A fresh regenerate run should clear the existing generated markdown files in that method folder before writing the new output.

The script treats `--method-name` as the canonical folder name for the run. It does not lowercase or restyle that name. If a conflicting sibling directory differs only by case, stop and resolve the naming conflict instead of generating a second folder.

The script always writes markdown links relative to the markdown file, for example:

```markdown
![Figure 2](images/page-003-figure-02.png)
*Figure 2. Model overview with retrieval and decoder branches.*
```

## Extraction strategy

Use this mental model when reading or modifying the script:

1. Parse text blocks and caption candidates from the PDF with PyMuPDF.
2. Propose base table regions with `pdfplumber` on born-digital PDFs.
3. Refine those regions with `PyMuPDF` text blocks and drawing objects, preferring shrink-to-content over broad expansion.
4. Propose visual regions from rendered-page layout objects instead of raw embedded-image bytes.
5. Match each `Figure`/`Fig.`/`Table` caption to the nearest plausible region on the same page.
6. Crop the rendered page region and save it into `images/`.
7. Insert a relative markdown image link close to the caption location.
8. If a MinerU skeleton is available, preserve its section hierarchy and inject links into that markdown instead of regenerating structure from scratch.

## Practical guidance

- If the user asks only for paper summarization, do not switch to extraction just because the input is a PDF.
- Use extraction to support explanation, not to replace explanation.
- For architecture/module questions, prefer extracting only the relevant figure or table when possible instead of converting the whole PDF to markdown.
- Keep captions in markdown even when the image crop itself already contains some visible caption text.
- When a caption cannot be matched into a provided skeleton markdown, append the extracted asset with its caption near the end rather than dropping it silently.
- If the user asks to regenerate or re-extract, remove the previous generated extraction outputs for that method folder before writing new ones.
- For scanned PDFs, be explicit that section hierarchy preservation depends on the OCR/text backbone. MinerU is the preferred path here.
- For tables in born-digital PDFs, prefer `pdfplumber` base proposals plus `PyMuPDF` text/drawing refinement.
- Prefer shrinking oversized table regions to table-content bounds over broad outward expansion.
- If no reliable table region exists on a page, skip that table crop rather than falling back to a whole-page or generic visual crop.
- For figures, prefer the closest rendered visual region near the caption, usually above the caption.
- For tables, captions are often above the table, so the cropped region is often below the caption.

## Example commands

Born-digital PDF:

```bash
python scripts/extract_pdf_figures.py \
  --pdf input/paper.pdf \
  --out-dir output \
  --method-name detr
```

MinerU-backed scanned PDF workflow:

```bash
python scripts/extract_pdf_figures.py \
  --pdf input/scanned-paper.pdf \
  --skeleton-markdown output/mineru/paper.md \
  --out-dir output \
  --method-name mineru-layoutlmv3 \
  --force-regenerate
```

## Reporting expectations

When you use this workflow in a user-facing task, report:

- whether the markdown came from a MinerU skeleton or was generated directly from the PDF
- which method-named folder was used for this run
- where the output markdown was saved
- where the `images/` directory was saved
- how many figure/table assets were extracted
- why visual extraction was needed for the user's question
- whether this was a fresh regenerate run
- any obvious failure modes, such as unmatched captions or sparse text in a scanned PDF without OCR
