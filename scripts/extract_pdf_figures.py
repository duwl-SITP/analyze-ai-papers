#!/usr/bin/env python3
"""Extract figure and table crops from a PDF and emit markdown with relative links."""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import statistics
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - runtime dependency check
    fitz = None

try:
    import pdfplumber
except ImportError:  # pragma: no cover - runtime dependency check
    pdfplumber = None


CAPTION_RE = re.compile(
    r"^\s*(?P<kind>Figure|Fig\.?|Table)\s*(?P<id>[A-Za-z0-9.\-]*)\s*[:.]?\s*(?P<rest>.*\S)?\s*$",
    re.IGNORECASE,
)
SUBPLOT_LABEL_RE = re.compile(
    r"^\s*(?:\((?P<label_paren>[A-Za-z])\)|(?P<label_plain>[A-Za-z])\))\s*(?P<rest>.*\S)?\s*$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)*)\s+\S")
KNOWN_SECTION_TITLES = {
    "abstract",
    "introduction",
    "related work",
    "background",
    "method",
    "methods",
    "approach",
    "experiments",
    "experimental setup",
    "results",
    "discussion",
    "limitations",
    "conclusion",
    "references",
    "appendix",
    "supplementary material",
}


@dataclass(frozen=True)
class TextBlock:
    page_index: int
    bbox: tuple[float, float, float, float]
    text: str
    max_font_size: float
    is_bold: bool


@dataclass(frozen=True)
class CaptionCandidate:
    block: TextBlock
    blocks: tuple[TextBlock, ...]
    bbox: tuple[float, float, float, float]
    kind: str
    label: str
    caption_text: str


@dataclass(frozen=True)
class AssetRecord:
    page_index: int
    kind: str
    label: str
    caption_text: str
    image_path: Path
    rel_link: str
    anchor_text: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract figure/table crops from a PDF, create one method-named "
            "artifact folder, save images/ there, and write markdown with "
            "relative image links."
        )
    )
    parser.add_argument("--pdf", required=True, help="Source PDF path.")
    parser.add_argument(
        "--out-dir",
        required=True,
        help=(
            "Parent output directory. The script creates one method-named artifact "
            "folder under this directory and writes markdown plus images/ there."
        ),
    )
    parser.add_argument(
        "--method-name",
        help=(
            "Optional method or model name used for the artifact folder. "
            "If omitted, the script falls back to the PDF filename stem."
        ),
    )
    parser.add_argument(
        "--markdown-name",
        default="paper.md",
        help=(
            "Markdown filename only to write under the method folder. "
            "Path components are not allowed. Default: paper.md"
        ),
    )
    parser.add_argument(
        "--skeleton-markdown",
        help=(
            "Optional markdown skeleton, typically produced by MinerU. "
            "When provided, section hierarchy is preserved and image links are injected there."
        ),
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=220,
        help="Render DPI for page-region crops. Default: 220",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=8.0,
        help="Extra PDF-point margin around matched crop regions. Default: 8",
    )
    parser.add_argument(
        "--force-regenerate",
        action="store_true",
        help=(
            "Remove previously generated markdown and images for this method folder "
            "before writing new extraction outputs."
        ),
    )
    parser.add_argument(
        "--debug-captions",
        action="store_true",
        help="Print detected figure/table captions to stderr before crop matching.",
    )
    parser.add_argument(
        "--debug-image-blocks",
        action="store_true",
        help="Print collected raw image blocks and final figure boxes to stderr for each page.",
    )
    return parser.parse_args(argv)


def require_dependencies() -> None:
    missing = []
    if fitz is None:
        missing.append("PyMuPDF")
    if pdfplumber is None:
        missing.append("pdfplumber")
    if missing:
        missing_csv = ", ".join(missing)
        raise SystemExit(
            f"Missing required dependencies: {missing_csv}. "
            "Install them before running this script."
        )


def normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("ﬁ", "fi").replace("ﬂ", "fl")
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9 ]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def validate_artifact_name(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise SystemExit("Artifact folder name must not be empty.")
    if cleaned in {".", ".."}:
        raise SystemExit(
            "Artifact folder name must not be '.' or '..'."
        )
    if "/" in cleaned or "\\" in cleaned:
        raise SystemExit(
            "Artifact folder name must not contain path separators."
        )
    if "\x00" in cleaned:
        raise SystemExit(
            "Artifact folder name must not contain NUL bytes."
        )
    return cleaned


def validate_markdown_name(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise SystemExit("Markdown filename must not be empty.")
    if cleaned in {".", ".."}:
        raise SystemExit("Markdown filename must not be '.' or '..'.")
    if "/" in cleaned or "\\" in cleaned:
        raise SystemExit(
            "Markdown filename must be a filename only and must not contain path separators."
        )
    if "\x00" in cleaned:
        raise SystemExit("Markdown filename must not contain NUL bytes.")
    return cleaned


def resolve_method_dir_name(pdf_path: Path, method_name: str | None) -> str:
    source_name = method_name if method_name is not None else pdf_path.stem
    return validate_artifact_name(source_name)


def ensure_no_case_conflict(base_out_dir: Path, method_dir_name: str) -> None:
    if not base_out_dir.exists():
        return
    target_key = method_dir_name.casefold()
    conflicts = sorted(
        candidate.name
        for candidate in base_out_dir.iterdir()
        if candidate.is_dir()
        and candidate.name.casefold() == target_key
        and candidate.name != method_dir_name
    )
    if conflicts:
        conflict_list = ", ".join(conflicts)
        raise SystemExit(
            "Conflicting artifact folders differ only by case: "
            f"{conflict_list} vs {method_dir_name}. "
            "Use one canonical folder name and remove or rename the conflicting directory."
        )


def prepare_method_dir(
    base_out_dir: Path,
    method_dir_name: str,
    markdown_name: str,
    force_regenerate: bool,
) -> tuple[Path, Path]:
    ensure_no_case_conflict(base_out_dir, method_dir_name)
    method_dir = base_out_dir / method_dir_name
    markdown_path = method_dir / markdown_name
    images_dir = method_dir / "images"

    if force_regenerate and method_dir.exists():
        for stale_markdown in method_dir.glob("*.md"):
            stale_markdown.unlink()
        if images_dir.exists():
            shutil.rmtree(images_dir)

    method_dir.mkdir(parents=True, exist_ok=True)
    return method_dir, markdown_path


def block_text_from_dict(block: dict) -> tuple[str, float, bool]:
    line_texts = []
    font_sizes = []
    bold_hits = 0
    span_count = 0
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        if not spans:
            continue
        text = "".join(span.get("text", "") for span in spans).strip()
        if not text:
            continue
        line_texts.append(text)
        for span in spans:
            span_count += 1
            font_sizes.append(float(span.get("size", 0.0) or 0.0))
            font_name = str(span.get("font", "")).lower()
            flags = int(span.get("flags", 0) or 0)
            if "bold" in font_name or (flags & 16):
                bold_hits += 1
    text = re.sub(r"\s+", " ", " ".join(line_texts)).strip()
    max_size = max(font_sizes) if font_sizes else 0.0
    is_bold = span_count > 0 and bold_hits >= max(1, span_count // 2)
    return text, max_size, is_bold


def extract_text_blocks(doc) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for page_index, page in enumerate(doc):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            text, max_size, is_bold = block_text_from_dict(block)
            if not text:
                continue
            bbox = tuple(float(v) for v in block.get("bbox", (0, 0, 0, 0)))
            blocks.append(
                TextBlock(
                    page_index=page_index,
                    bbox=bbox,
                    text=text,
                    max_font_size=max_size,
                    is_bold=is_bold,
                )
            )
    return blocks


def body_font_size(blocks: Sequence[TextBlock]) -> float:
    sizes = [block.max_font_size for block in blocks if block.max_font_size > 0]
    if not sizes:
        return 10.0
    return statistics.median(sizes)


def block_key(block: TextBlock) -> tuple[int, tuple[float, float, float, float], str]:
    return (block.page_index, block.bbox, block.text)


def join_block_texts(blocks: Sequence[TextBlock]) -> str:
    return " ".join(block.text.strip() for block in blocks if block.text.strip()).strip()


def union_boxes(boxes: Sequence[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    current = boxes[0]
    for box in boxes[1:]:
        current = union_box(current, box)
    return current


def edge_alignment_delta(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    return axis_alignment_delta(a[0], a[2], b[0], b[2])


def vertical_alignment_delta(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    return axis_alignment_delta(a[1], a[3], b[1], b[3])


def subplot_label_id(text: str) -> str | None:
    match = SUBPLOT_LABEL_RE.match(text.strip())
    if not match:
        return None
    label = match.group("label_paren") or match.group("label_plain")
    if label is None:
        return None
    return label.lower()


def looks_subplot_label(text: str) -> bool:
    return subplot_label_id(text) is not None


def is_caption_continuation(
    anchor_block: TextBlock,
    current_box: tuple[float, float, float, float],
    candidate: TextBlock,
    body_size: float,
    page_width: float,
) -> bool:
    if CAPTION_RE.match(candidate.text):
        return False
    if candidate.bbox[1] + 1.0 < current_box[3]:
        return False

    max_vertical_gap = max(10.0, body_size * 0.8)
    if vertical_gap(candidate.bbox, current_box) > max_vertical_gap:
        return False

    if heading_level(candidate, body_size) is not None:
        return False

    if candidate.max_font_size > max(anchor_block.max_font_size * 1.3, body_size * 1.35):
        return False

    region_overlap = horizontal_overlap(candidate.bbox, current_box)
    anchor_overlap = horizontal_overlap(candidate.bbox, anchor_block.bbox)
    edge_tol = max(18.0, page_width * 0.03)
    if max(region_overlap, anchor_overlap) < 0.55 and edge_alignment_delta(candidate.bbox, current_box) > edge_tol:
        return False

    stripped = candidate.text.strip()
    if not stripped:
        return False
    if stripped.endswith(":") and len(stripped.split()) <= 16:
        return False
    return True


def detect_captions(blocks: Sequence[TextBlock]) -> dict[tuple[int, str], CaptionCandidate]:
    captions: dict[tuple[int, str], CaptionCandidate] = {}
    blocks_by_page: dict[int, list[TextBlock]] = {}
    for block in blocks:
        blocks_by_page.setdefault(block.page_index, []).append(block)

    for page_index, page_blocks in blocks_by_page.items():
        ordered = sorted(page_blocks, key=lambda item: (item.bbox[1], item.bbox[0], item.bbox[3], item.bbox[2]))
        consumed: set[tuple[int, tuple[float, float, float, float], str]] = set()
        page_body_size = body_font_size(ordered)
        page_width = max((block.bbox[2] for block in ordered), default=600.0)

        for index, block in enumerate(ordered):
            block_id = block_key(block)
            if block_id in consumed:
                continue

            match = CAPTION_RE.match(block.text)
            if not match:
                continue

            raw_kind = match.group("kind").lower()
            kind = "table" if raw_kind.startswith("table") else "figure"
            label_id = (match.group("id") or "").strip()
            label_prefix = "Table" if kind == "table" else "Figure"
            label = f"{label_prefix} {label_id}".strip()

            caption_blocks = [block]
            current_box = block.bbox
            for candidate in ordered[index + 1:]:
                candidate_id = block_key(candidate)
                if candidate_id in consumed:
                    continue
                if candidate.page_index != page_index:
                    break
                if not is_caption_continuation(
                    anchor_block=block,
                    current_box=current_box,
                    candidate=candidate,
                    body_size=page_body_size,
                    page_width=page_width,
                ):
                    if candidate.bbox[1] > current_box[3] + max(10.0, page_body_size * 0.8):
                        break
                    continue
                caption_blocks.append(candidate)
                current_box = union_box(current_box, candidate.bbox)

            consumed.update(block_key(item) for item in caption_blocks)
            caption_bbox = union_boxes([item.bbox for item in caption_blocks])
            captions[(page_index, block.text)] = CaptionCandidate(
                block=block,
                blocks=tuple(caption_blocks),
                bbox=caption_bbox,
                kind=kind,
                label=label,
                caption_text=join_block_texts(caption_blocks),
            )
    return captions


def emit_detected_captions(captions: dict[tuple[int, str], CaptionCandidate]) -> None:
    if not captions:
        print("[debug-captions] no captions detected", file=sys.stderr)
        return

    print(f"[debug-captions] detected {len(captions)} captions", file=sys.stderr)
    for caption in sorted(captions.values(), key=lambda item: (item.block.page_index, item.bbox[1], item.bbox[0])):
        x0, y0, x1, y1 = caption.bbox
        print(
            (
                f"[debug-captions] page={caption.block.page_index + 1} "
                f"kind={caption.kind} label={caption.label!r} "
                f"bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}) "
                f"text={caption.caption_text!r}"
            ),
            file=sys.stderr,
        )


def emit_detected_image_blocks(
    page_index: int,
    image_boxes: Sequence[tuple[float, float, float, float]],
    figure_boxes: Sequence[tuple[float, float, float, float]],
) -> None:
    print(
        f"[debug-image-blocks] page={page_index + 1} raw_image_blocks={len(image_boxes)} final_figure_boxes={len(figure_boxes)}",
        file=sys.stderr,
    )
    for index, box in enumerate(image_boxes, start=1):
        x0, y0, x1, y1 = box
        print(
            f"[debug-image-blocks] page={page_index + 1} image_block[{index}] bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})",
            file=sys.stderr,
        )
    for index, box in enumerate(figure_boxes, start=1):
        x0, y0, x1, y1 = box
        print(
            f"[debug-image-blocks] page={page_index + 1} figure_box[{index}] bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})",
            file=sys.stderr,
        )


def rect_area(rect: tuple[float, float, float, float]) -> float:
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def horizontal_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    overlap = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    denom = min(max(1.0, a[2] - a[0]), max(1.0, b[2] - b[0]))
    return overlap / denom


def center_x(box: tuple[float, float, float, float]) -> float:
    return (box[0] + box[2]) / 2.0


def center_y(box: tuple[float, float, float, float]) -> float:
    return (box[1] + box[3]) / 2.0


def vertical_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    overlap = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    denom = min(max(1.0, a[3] - a[1]), max(1.0, b[3] - b[1]))
    return overlap / denom


def axis_gap(a0: float, a1: float, b0: float, b1: float) -> float:
    if a1 < b0:
        return b0 - a1
    if b1 < a0:
        return a0 - b1
    return 0.0


def axis_alignment_delta(a0: float, a1: float, b0: float, b1: float) -> float:
    return min(abs(a0 - b0), abs(a1 - b1), abs(((a0 + a1) / 2.0) - ((b0 + b1) / 2.0)))


def horizontal_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    return axis_gap(a[0], a[2], b[0], b[2])


def vertical_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    return axis_gap(a[1], a[3], b[1], b[3])


def boxes_close(a: tuple[float, float, float, float], b: tuple[float, float, float, float], gap: float) -> bool:
    return not (
        a[2] + gap < b[0]
        or b[2] + gap < a[0]
        or a[3] + gap < b[1]
        or b[3] + gap < a[1]
    )


def union_box(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def merge_boxes(boxes: Iterable[tuple[float, float, float, float]], gap: float = 10.0) -> list[tuple[float, float, float, float]]:
    merged: list[tuple[float, float, float, float]] = []
    for box in sorted(boxes, key=lambda item: (item[1], item[0], item[3], item[2])):
        if rect_area(box) <= 0:
            continue
        consumed = False
        for index, current in enumerate(merged):
            if boxes_close(current, box, gap):
                merged[index] = union_box(current, box)
                consumed = True
                break
        if not consumed:
            merged.append(box)

    changed = True
    while changed:
        changed = False
        result: list[tuple[float, float, float, float]] = []
        while merged:
            current = merged.pop(0)
            merged_with_current = False
            for other_index, other in enumerate(merged):
                if boxes_close(current, other, gap):
                    merged[other_index] = union_box(current, other)
                    merged_with_current = True
                    changed = True
                    break
            if not merged_with_current:
                result.append(current)
        merged = result
    return merged


def merge_table_boxes(
    boxes: Iterable[tuple[float, float, float, float]],
    page_width: float,
    page_height: float,
) -> list[tuple[float, float, float, float]]:
    merged = [box for box in boxes if rect_area(box) > 0]
    x_tol = max(12.0, page_width * 0.03)
    max_vertical_gap = max(24.0, page_height * 0.03)
    max_horizontal_gap = max(18.0, page_width * 0.025)

    def should_merge(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
        h_overlap = horizontal_overlap(a, b)
        v_overlap = vertical_overlap(a, b)
        v_gap = vertical_gap(a, b)
        h_gap = horizontal_gap(a, b)
        left_aligned = abs(a[0] - b[0]) <= x_tol
        right_aligned = abs(a[2] - b[2]) <= x_tol
        center_aligned = abs(((a[0] + a[2]) / 2.0) - ((b[0] + b[2]) / 2.0)) <= x_tol * 1.4

        if h_overlap >= 0.72 and v_gap <= max_vertical_gap:
            return True
        if h_overlap >= 0.45 and v_gap <= max_vertical_gap and (left_aligned or right_aligned or center_aligned):
            return True
        if v_overlap >= 0.65 and h_gap <= max_horizontal_gap:
            return True
        return False

    changed = True
    while changed:
        changed = False
        result: list[tuple[float, float, float, float]] = []
        for box in sorted(merged, key=lambda item: (item[1], item[0], item[3], item[2])):
            merged_with_existing = False
            for index, current in enumerate(result):
                if should_merge(current, box):
                    result[index] = union_box(current, box)
                    merged_with_existing = True
                    changed = True
                    break
            if not merged_with_existing:
                result.append(box)
        merged = result
    return merged


def collect_table_drawing_boxes(page) -> list[tuple[float, float, float, float]]:
    page_area = rect_area((page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1))
    boxes = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        bbox = (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        line_width = float(drawing.get("width", 0.0) or 0.0)
        is_thin_horizontal = width >= 36 and height <= 4
        is_thin_vertical = height >= 36 and width <= 4
        is_border_rect = (
            width >= 36
            and height >= 24
            and line_width <= 2.0
            and rect_area(bbox) <= page_area * 0.55
        )
        if is_thin_horizontal or is_thin_vertical or is_border_rect:
            boxes.append(bbox)
    return merge_table_boxes(
        boxes,
        page_width=page.rect.width,
        page_height=page.rect.height,
    )


def collect_table_text_boxes(
    page_blocks: Sequence[TextBlock],
    page_width: float,
    page_height: float,
) -> list[tuple[float, float, float, float]]:
    candidate_blocks = [
        block
        for block in page_blocks
        if looks_table_like_text(block.text) and box_width(block.bbox) <= page_width * 0.96
    ]
    if not candidate_blocks:
        return []

    x_tol = max(10.0, page_width * 0.025)
    max_vertical_gap = max(14.0, page_height * 0.018)
    clusters: list[dict[str, object]] = []

    def should_merge_text_box(
        current: tuple[float, float, float, float],
        other: tuple[float, float, float, float],
    ) -> bool:
        h_overlap = horizontal_overlap(current, other)
        v_gap = vertical_gap(current, other)
        left_aligned = abs(current[0] - other[0]) <= x_tol
        right_aligned = abs(current[2] - other[2]) <= x_tol
        center_aligned = abs(((current[0] + current[2]) / 2.0) - ((other[0] + other[2]) / 2.0)) <= x_tol * 1.25
        return (
            h_overlap >= 0.55 and v_gap <= max_vertical_gap and (left_aligned or right_aligned or center_aligned)
        ) or (
            h_overlap >= 0.8 and v_gap <= max_vertical_gap * 1.5
        )

    for block in sorted(candidate_blocks, key=lambda item: (item.bbox[1], item.bbox[0])):
        merged = False
        for cluster in clusters:
            current_bbox = cluster["bbox"]
            assert isinstance(current_bbox, tuple)
            if should_merge_text_box(current_bbox, block.bbox):
                cluster["bbox"] = union_box(current_bbox, block.bbox)
                cluster["count"] = int(cluster["count"]) + 1
                merged = True
                break
        if not merged:
            clusters.append({"bbox": block.bbox, "count": 1})

    results = []
    for cluster in clusters:
        bbox = cluster["bbox"]
        count = int(cluster["count"])
        assert isinstance(bbox, tuple)
        if count >= 3 or (count >= 2 and (box_width(bbox) >= page_width * 0.22 or box_height(bbox) >= 40.0)):
            results.append(bbox)
    return merge_table_boxes(results, page_width=page_width, page_height=page_height)


def collect_visual_boxes(
    page,
    *,
    debug_image_blocks: bool = False,
    page_index: int | None = None,
) -> list[tuple[float, float, float, float]]:
    page_dict = page.get_text("dict")
    page_area = rect_area((page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1))

    def looks_page_sized_container(bbox: tuple[float, float, float, float]) -> bool:
        width = box_width(bbox)
        height = box_height(bbox)
        x_margin = max(12.0, page.rect.width * 0.02)
        y_margin = max(12.0, page.rect.height * 0.02)
        near_left = bbox[0] <= page.rect.x0 + x_margin
        near_right = bbox[2] >= page.rect.x1 - x_margin
        near_top = bbox[1] <= page.rect.y0 + y_margin
        near_bottom = bbox[3] >= page.rect.y1 - y_margin
        return (
            width >= page.rect.width * 0.92 and height >= page.rect.height * 0.92
        ) or (
            near_left and near_right and height >= page.rect.height * 0.88
        ) or (
            near_top and near_bottom and width >= page.rect.width * 0.88
        )

    image_boxes = []
    for block in page_dict.get("blocks", []):
        if block.get("type") == 1:
            bbox = tuple(float(v) for v in block.get("bbox", (0, 0, 0, 0)))
            if rect_area(bbox) >= 800:
                image_boxes.append(bbox)

    drawing_boxes = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        bbox = (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        area = rect_area(bbox)
        line_width = float(drawing.get("width", 0.0) or 0.0)
        if width < 18 or height < 18 or area < 500:
            continue

        large_container = (
            line_width <= 2.5
            and area >= page_area * 0.22
            and (width >= page.rect.width * 0.72 or height >= page.rect.height * 0.4)
        )
        if image_boxes:
            related_to_image = any(
                (horizontal_overlap(bbox, image_box) >= 0.5 and vertical_overlap(bbox, image_box) >= 0.5)
                or boxes_close(bbox, image_box, gap=8.0)
                for image_box in image_boxes
            )
            if not related_to_image and large_container and looks_page_sized_container(bbox):
                continue
            if related_to_image or not large_container:
                drawing_boxes.append(bbox)
            elif not looks_page_sized_container(bbox):
                drawing_boxes.append(bbox)
            continue

        if large_container and area >= page_area * 0.32 and looks_page_sized_container(bbox):
            continue
        drawing_boxes.append(bbox)

    figure_boxes = merge_boxes(image_boxes + drawing_boxes, gap=6.0)
    if debug_image_blocks and page_index is not None:
        emit_detected_image_blocks(
            page_index=page_index,
            image_boxes=image_boxes,
            figure_boxes=figure_boxes,
        )
    return figure_boxes


def build_table_box_from_supports(
    base_box: tuple[float, float, float, float],
    support_boxes: Sequence[tuple[float, float, float, float]],
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float]:
    matched_supports = []
    x_tol = max(12.0, page_width * 0.03)
    max_vertical_gap = max(20.0, page_height * 0.025)
    for box in support_boxes:
        if horizontal_overlap(box, base_box) >= 0.35 and vertical_gap(box, base_box) <= max_vertical_gap:
            matched_supports.append(box)
            continue
        center_aligned = abs(((box[0] + box[2]) / 2.0) - ((base_box[0] + base_box[2]) / 2.0)) <= x_tol
        edge_aligned = abs(box[0] - base_box[0]) <= x_tol or abs(box[2] - base_box[2]) <= x_tol
        if (center_aligned or edge_aligned) and vertical_gap(box, base_box) <= max_vertical_gap:
            matched_supports.append(box)

    if not matched_supports:
        return base_box

    content_box = matched_supports[0]
    for box in matched_supports[1:]:
        content_box = union_box(content_box, box)

    base_w = box_width(base_box)
    base_h = box_height(base_box)
    content_w = box_width(content_box)
    content_h = box_height(content_box)
    if content_w < base_w * 0.35 and content_h < base_h * 0.35:
        return base_box

    pad_x = max(4.0, page_width * 0.005)
    pad_y = max(4.0, page_height * 0.004)
    return (
        content_box[0] - pad_x,
        content_box[1] - pad_y,
        content_box[2] + pad_x,
        content_box[3] + pad_y,
    )


def collect_table_boxes(
    plumber_page,
    page,
    page_blocks: Sequence[TextBlock],
) -> list[tuple[float, float, float, float]]:
    try:
        tables = plumber_page.find_tables()
    except Exception:
        tables = []

    plumber_boxes = []
    for table in tables:
        bbox = tuple(float(v) for v in table.bbox)
        if rect_area(bbox) >= 1000:
            plumber_boxes.append(bbox)

    drawing_boxes = collect_table_drawing_boxes(page)
    text_boxes = collect_table_text_boxes(
        page_blocks,
        page_width=page.rect.width,
        page_height=page.rect.height,
    )
    support_boxes = drawing_boxes + text_boxes
    refined_boxes = [
        build_table_box_from_supports(
            box,
            support_boxes=support_boxes,
            page_width=page.rect.width,
            page_height=page.rect.height,
        )
        for box in plumber_boxes
    ]

    candidate_boxes = list(refined_boxes)
    for box in support_boxes:
        if not any(
            horizontal_overlap(box, existing) >= 0.35 and vertical_gap(box, existing) <= max(22.0, page.rect.height * 0.025)
            for existing in refined_boxes
        ):
            candidate_boxes.append(box)

    return merge_table_boxes(
        candidate_boxes,
        page_width=page.rect.width,
        page_height=page.rect.height,
    )


def looks_table_like_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if len(stripped) > 180:
        return False
    if CAPTION_RE.match(stripped):
        return False
    words = stripped.split()
    if len(words) > 24 and stripped.endswith((".", "?", "!")):
        return False
    numeric_tokens = sum(any(char.isdigit() for char in token) for token in words)
    punctuation_hits = sum(stripped.count(char) for char in ("%","/","|","±","(",")","[","]"))
    if numeric_tokens >= 2 or punctuation_hits >= 3:
        return True
    return len(words) <= 12 and not stripped.endswith((".", "?", "!"))


def box_height(box: tuple[float, float, float, float]) -> float:
    return max(0.0, box[3] - box[1])


def box_width(box: tuple[float, float, float, float]) -> float:
    return max(0.0, box[2] - box[0])


def caption_block_keys(caption: CaptionCandidate) -> set[tuple[int, tuple[float, float, float, float], str]]:
    return {block_key(block) for block in caption.blocks}


def should_skip_caption_related_block(caption: CaptionCandidate, block: TextBlock) -> bool:
    return block_key(block) in caption_block_keys(caption) or CAPTION_RE.match(block.text) is not None


def looks_running_text_block(
    block: TextBlock,
    page_width: float,
    body_size: float,
) -> bool:
    text = block.text.strip()
    if not text or len(text) > 180:
        return False
    width = box_width(block.bbox)
    height = box_height(block.bbox)
    center_x = (block.bbox[0] + block.bbox[2]) / 2.0
    centered = abs(center_x - page_width / 2.0) <= page_width * 0.18
    return height <= max(28.0, body_size * 2.8) and (width >= page_width * 0.4 or centered)


def caption_box_distance(
    caption_box: tuple[float, float, float, float],
    box: tuple[float, float, float, float],
    direction: str,
) -> float:
    if direction == "above":
        return caption_box[1] - box[3]
    return box[1] - caption_box[3]


def trim_box_for_caption_matching(
    box: tuple[float, float, float, float],
    caption_box: tuple[float, float, float, float],
    direction: str,
    pad: float = 2.0,
) -> tuple[float, float, float, float] | None:
    if direction == "above":
        if box[3] <= caption_box[1]:
            return box
        trimmed = (box[0], box[1], box[2], min(box[3], caption_box[1] - pad))
    else:
        if box[1] >= caption_box[3]:
            return box
        trimmed = (box[0], max(box[1], caption_box[3] + pad), box[2], box[3])

    if box_height(trimmed) < max(18.0, box_height(box) * 0.22):
        return None
    return trimmed


def score_box_for_caption(
    caption_box: tuple[float, float, float, float],
    box: tuple[float, float, float, float],
    direction: str,
    max_primary_distance: float,
) -> float | None:
    match_box = trim_box_for_caption_matching(box, caption_box, direction)
    if match_box is None:
        return None

    distance = caption_box_distance(caption_box, match_box, direction)
    if distance < -6 or distance > max_primary_distance:
        return None
    overlap = horizontal_overlap(caption_box, match_box)
    if overlap <= 0.1:
        return None
    center_penalty = abs(center_x(caption_box) - center_x(match_box)) / 10.0
    return distance + center_penalty - overlap * 40.0


def select_best_box_for_caption(
    primary: Sequence[tuple[float, float, float, float]],
    caption_box: tuple[float, float, float, float],
    preferred_direction: str,
    max_primary_distance: float,
) -> tuple[tuple[float, float, float, float], str] | None:
    for direction in (preferred_direction, "below" if preferred_direction == "above" else "above"):
        candidates = []
        for box in primary:
            region_score = score_box_for_caption(
                caption_box=caption_box,
                box=box,
                direction=direction,
                max_primary_distance=max_primary_distance,
            )
            if region_score is not None:
                candidates.append((region_score, box))
        if candidates:
            best_score, best_box = min(candidates, key=lambda item: item[0])
            _ = best_score
            return best_box, direction
    return None


def figure_box_is_in_caption_band(
    caption_box: tuple[float, float, float, float],
    box: tuple[float, float, float, float],
    direction: str,
    max_primary_distance: float,
    page_width: float,
) -> bool:
    distance = caption_box_distance(caption_box, box, direction)
    if distance < -24 or distance > max_primary_distance * 1.7:
        return False
    overlap = horizontal_overlap(caption_box, box)
    center_aligned = abs(center_x(caption_box) - center_x(box)) <= page_width * 0.42
    return overlap >= 0.05 or center_aligned


def figure_boxes_are_neighbors(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    page_width: float,
    page_height: float,
) -> bool:
    horizontal_gap_tol = max(24.0, page_width * 0.08)
    vertical_gap_tol = max(24.0, page_height * 0.05)
    align_tol = max(16.0, page_width * 0.025)

    same_row = horizontal_gap(a, b) <= horizontal_gap_tol and vertical_alignment_delta(a, b) <= align_tol
    same_column = vertical_gap(a, b) <= vertical_gap_tol and edge_alignment_delta(a, b) <= align_tol
    compact_overlap = boxes_close(a, b, gap=min(horizontal_gap_tol, vertical_gap_tol) * 0.5) and (
        horizontal_overlap(a, b) >= 0.35 or vertical_overlap(a, b) >= 0.35
    )
    return same_row or same_column or compact_overlap


def has_text_barrier_between_boxes(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    page_blocks: Sequence[TextBlock],
    body_size: float,
) -> bool:
    combined = union_box(a, b)
    row_like = horizontal_gap(a, b) > 0 and vertical_alignment_delta(a, b) <= max(16.0, body_size * 1.6)
    column_like = vertical_gap(a, b) > 0 and edge_alignment_delta(a, b) <= max(16.0, body_size * 1.6)

    for block in page_blocks:
        text = block.text.strip()
        if not text or CAPTION_RE.match(text) or looks_subplot_label(text):
            continue
        if len(text.split()) < 3 and box_width(block.bbox) < 42.0 and box_height(block.bbox) < max(14.0, body_size * 1.2):
            continue

        if row_like:
            left_box, right_box = sorted((a, b), key=lambda item: item[0])
            if (
                block.bbox[0] >= left_box[2] - 2.0
                and block.bbox[2] <= right_box[0] + 2.0
                and vertical_overlap(block.bbox, combined) >= 0.45
            ):
                return True

        if column_like:
            top_box, bottom_box = sorted((a, b), key=lambda item: item[1])
            if (
                block.bbox[1] >= top_box[3] - 2.0
                and block.bbox[3] <= bottom_box[1] + 2.0
                and horizontal_overlap(block.bbox, combined) >= 0.45
                and (len(text.split()) >= 3 or box_height(block.bbox) >= max(16.0, body_size * 1.2))
            ):
                return True

    return False


def count_subplot_labels_near_boxes(
    boxes: Sequence[tuple[float, float, float, float]],
    page_blocks: Sequence[TextBlock],
    page_width: float,
    page_height: float,
) -> set[str]:
    labels: set[str] = set()
    x_tol = max(12.0, page_width * 0.02)
    vertical_gap_tol = max(30.0, page_height * 0.04)

    for block in page_blocks:
        label = subplot_label_id(block.text)
        if label is None:
            continue
        for box in boxes:
            horizontally_near = horizontal_overlap(block.bbox, box) >= 0.2 or abs(center_x(block.bbox) - center_x(box)) <= max(
                x_tol,
                box_width(box) * 0.35,
            )
            vertically_near = (
                -6.0 <= block.bbox[1] - box[3] <= vertical_gap_tol
                or -6.0 <= box[1] - block.bbox[3] <= vertical_gap_tol
                or vertical_overlap(block.bbox, box) >= 0.2
            )
            if horizontally_near and vertically_near:
                labels.add(label)
                break
    return labels


def group_figure_boxes_for_caption(
    caption: CaptionCandidate,
    figure_boxes: Sequence[tuple[float, float, float, float]],
    page_blocks: Sequence[TextBlock],
    page_width: float,
    page_height: float,
    seed_box: tuple[float, float, float, float],
    direction: str,
    max_primary_distance: float,
) -> tuple[float, float, float, float]:
    caption_box = caption.bbox
    seed_area = rect_area(seed_box)
    body_size = body_font_size(page_blocks)

    candidate_boxes = [
        box
        for box in figure_boxes
        if box != seed_box
        and figure_box_is_in_caption_band(
            caption_box=caption_box,
            box=box,
            direction=direction,
            max_primary_distance=max_primary_distance,
            page_width=page_width,
        )
    ]

    group = [seed_box]
    current_union = seed_box
    changed = True
    while changed:
        changed = False
        for box in list(candidate_boxes):
            if rect_area(box) < max(350.0, seed_area * 0.18) and (
                box_width(box) < box_width(seed_box) * 0.45
                or box_height(box) < box_height(seed_box) * 0.45
            ):
                continue

            if horizontal_overlap(box, caption_box) < 0.03 and abs(center_x(box) - center_x(current_union)) > max(
                box_width(current_union) * 0.9,
                page_width * 0.18,
            ):
                continue

            joinable = False
            for existing in group:
                if not figure_boxes_are_neighbors(existing, box, page_width=page_width, page_height=page_height):
                    continue
                if has_text_barrier_between_boxes(existing, box, page_blocks=page_blocks, body_size=body_size):
                    continue
                joinable = True
                break

            if not joinable:
                continue

            group.append(box)
            candidate_boxes.remove(box)
            current_union = union_box(current_union, box)
            changed = True

    subplot_labels = count_subplot_labels_near_boxes(
        boxes=group,
        page_blocks=page_blocks,
        page_width=page_width,
        page_height=page_height,
    )
    if len(group) >= 3 or (len(group) >= 2 and len(subplot_labels) >= 2):
        return union_boxes(group)
    return seed_box


def find_table_region_from_caption_context(
    caption: CaptionCandidate,
    page_blocks: Sequence[TextBlock],
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float] | None:
    caption_box = caption.bbox
    x_tol = max(18.0, page_width * 0.03)
    max_start_gap = max(120.0, page_height * 0.12)
    max_vertical_gap = max(24.0, page_height * 0.03)
    pad_x = max(4.0, page_width * 0.005)
    pad_y = max(4.0, page_height * 0.004)

    candidate_blocks = []
    for block in sorted(page_blocks, key=lambda item: (item.bbox[1], item.bbox[0])):
        if should_skip_caption_related_block(caption, block):
            continue
        if not looks_table_like_text(block.text):
            continue
        if block.bbox[1] < caption_box[3] + 1.0:
            continue
        if block.bbox[1] - caption_box[3] > max_start_gap:
            continue

        overlap = horizontal_overlap(block.bbox, caption_box)
        aligned = edge_alignment_delta(block.bbox, caption_box) <= x_tol
        if overlap < 0.38 and not aligned:
            continue
        candidate_blocks.append(block)

    if not candidate_blocks:
        return None

    clusters: list[list[TextBlock]] = []
    current_cluster: list[TextBlock] = []
    current_box: tuple[float, float, float, float] | None = None

    for block in candidate_blocks:
        if not current_cluster:
            current_cluster = [block]
            current_box = block.bbox
            continue

        assert current_box is not None
        cluster_overlap = horizontal_overlap(block.bbox, current_box)
        cluster_aligned = edge_alignment_delta(block.bbox, current_box) <= x_tol
        if vertical_gap(block.bbox, current_box) <= max_vertical_gap and (cluster_overlap >= 0.45 or cluster_aligned):
            current_cluster.append(block)
            current_box = union_box(current_box, block.bbox)
            continue

        clusters.append(current_cluster)
        current_cluster = [block]
        current_box = block.bbox

    if current_cluster:
        clusters.append(current_cluster)

    best_score = None
    best_box = None
    for cluster in clusters:
        cluster_box = union_boxes([block.bbox for block in cluster])
        count = len(cluster)
        if count < 2 and box_width(cluster_box) < page_width * 0.45:
            continue
        distance = max(0.0, cluster_box[1] - caption_box[3])
        score = distance - count * 30.0 - box_width(cluster_box) / 18.0
        if best_score is None or score < best_score:
            best_score = score
            best_box = cluster_box

    if best_box is None:
        return None

    return (
        best_box[0] - pad_x,
        best_box[1] - pad_y,
        best_box[2] + pad_x,
        best_box[3] + pad_y,
    )


def refine_table_region(
    region: tuple[float, float, float, float],
    caption: CaptionCandidate,
    table_boxes: Sequence[tuple[float, float, float, float]],
    page_blocks: Sequence[TextBlock],
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float]:
    caption_box = caption.bbox
    caption_keys = caption_block_keys(caption)
    below_caption = center_y(region) >= center_y(caption_box)
    support_boxes: list[tuple[float, float, float, float]] = []
    max_vertical_gap = max(18.0, page_height * 0.02)
    pad_x = max(4.0, page_width * 0.005)
    pad_y = max(4.0, page_height * 0.004)

    for box in table_boxes:
        if horizontal_overlap(box, region) >= 0.3 and vertical_gap(box, region) <= max_vertical_gap:
            support_boxes.append(box)

    for block in page_blocks:
        if not looks_table_like_text(block.text):
            continue
        if block_key(block) in caption_keys or CAPTION_RE.match(block.text):
            continue
        if below_caption and block.bbox[1] < caption_box[3] + 2:
            continue
        if not below_caption and block.bbox[3] > caption_box[1] - 2:
            continue
        if horizontal_overlap(block.bbox, region) < 0.35 and vertical_overlap(block.bbox, region) <= 0.1:
            continue
        if vertical_gap(block.bbox, region) > max_vertical_gap:
            continue
        support_boxes.append(block.bbox)

    if support_boxes:
        current = support_boxes[0]
        for box in support_boxes[1:]:
            current = union_box(current, box)
        current = (
            current[0] - pad_x,
            current[1] - pad_y,
            current[2] + pad_x,
            current[3] + pad_y,
        )
    else:
        current = region

    top_boundary = current[1]
    bottom_boundary = current[3]
    for block in page_blocks:
        if block_key(block) in caption_keys or CAPTION_RE.match(block.text):
            continue
        if looks_table_like_text(block.text):
            continue
        if horizontal_overlap(block.bbox, current) < 0.45:
            continue
        if block.bbox[1] <= top_boundary <= block.bbox[3]:
            top_boundary = max(top_boundary, block.bbox[3] + 2.0)
        if block.bbox[1] <= bottom_boundary <= block.bbox[3]:
            bottom_boundary = min(bottom_boundary, block.bbox[1] - 2.0)

    if bottom_boundary - top_boundary >= 18.0:
        current = (current[0], top_boundary, current[2], bottom_boundary)
    return current


def refine_figure_region(
    region: tuple[float, float, float, float],
    caption: CaptionCandidate,
    page_blocks: Sequence[TextBlock],
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float]:
    current = region
    caption_box = caption.bbox
    caption_keys = caption_block_keys(caption)
    body_size = body_font_size(page_blocks)
    top_boundary = current[1]
    bottom_boundary = current[3]
    edge_pad = 1.5
    edge_gap = max(36.0, page_height * 0.045)
    header_band_bottom = max(56.0, page_height * 0.08)

    for block in page_blocks:
        if block_key(block) in caption_keys or CAPTION_RE.match(block.text):
            continue
        if horizontal_overlap(block.bbox, current) < 0.45:
            continue
        if block.bbox[1] <= top_boundary <= block.bbox[3]:
            top_boundary = max(top_boundary, block.bbox[3] + edge_pad)

        if (
            current[1] <= header_band_bottom
            and block.bbox[1] <= header_band_bottom
            and block.bbox[3] <= current[1] + edge_gap
            and block.bbox[3] <= caption_box[1] - max(24.0, page_height * 0.03)
            and looks_running_text_block(block, page_width=page_width, body_size=body_size)
        ):
            top_boundary = max(top_boundary, block.bbox[3] + edge_pad)

    # Preserve the full bottom of a figure whenever possible; only the
    # matched caption should constrain the lower boundary.
    if bottom_boundary > caption_box[1]:
        bottom_boundary = min(bottom_boundary, caption_box[1] - edge_pad)
    if caption_box[3] > top_boundary and center_y(current) > center_y(caption_box):
        top_boundary = max(top_boundary, caption_box[3] + edge_pad)

    if bottom_boundary - top_boundary >= 18.0:
        return (current[0], top_boundary, current[2], bottom_boundary)
    return current


def trim_caption_overlap(
    region: tuple[float, float, float, float],
    caption_box: tuple[float, float, float, float],
    pad: float = 3.0,
) -> tuple[float, float, float, float]:
    if region[3] <= caption_box[1] or region[1] >= caption_box[3]:
        return region

    if center_y(region) <= center_y(caption_box):
        trimmed = (region[0], region[1], region[2], min(region[3], caption_box[1] - pad))
    else:
        trimmed = (region[0], max(region[1], caption_box[3] + pad), region[2], region[3])

    if trimmed[3] - trimmed[1] < 12:
        return region
    return trimmed


def choose_region(
    caption: CaptionCandidate,
    figure_boxes: Sequence[tuple[float, float, float, float]],
    table_boxes: Sequence[tuple[float, float, float, float]],
    page_blocks: Sequence[TextBlock] | None = None,
    page_width: float | None = None,
    page_height: float | None = None,
) -> tuple[float, float, float, float] | None:
    caption_box = caption.bbox
    if caption.kind == "table":
        if table_boxes:
            primary = table_boxes
        elif page_blocks is not None and page_width is not None and page_height is not None:
            return find_table_region_from_caption_context(
                caption=caption,
                page_blocks=page_blocks,
                page_width=page_width,
                page_height=page_height,
            )
        else:
            return None
        preferred_direction = "below"
        max_primary_distance = 420.0
    else:
        primary = figure_boxes
        preferred_direction = "above"
        max_primary_distance = 320.0

    best = select_best_box_for_caption(
        primary=primary,
        caption_box=caption_box,
        preferred_direction=preferred_direction,
        max_primary_distance=max_primary_distance,
    )
    if best is None:
        return None

    best_box, best_direction = best
    if caption.kind == "figure" and page_blocks is not None and page_width is not None and page_height is not None:
        return group_figure_boxes_for_caption(
            caption=caption,
            figure_boxes=primary,
            page_blocks=page_blocks,
            page_width=page_width,
            page_height=page_height,
            seed_box=best_box,
            direction=best_direction,
            max_primary_distance=max_primary_distance,
        )
    return best_box


def clamp_box(
    box: tuple[float, float, float, float],
    page_rect,
    margin: float,
) -> tuple[float, float, float, float]:
    x0 = max(page_rect.x0, box[0] - margin)
    y0 = max(page_rect.y0, box[1] - margin)
    x1 = min(page_rect.x1, box[2] + margin)
    y1 = min(page_rect.y1, box[3] + margin)
    return (x0, y0, x1, y1)


def filename_slug(label: str, fallback_kind: str) -> str:
    text = normalize_text(label).replace(" ", "-")
    return text or fallback_kind


def render_crop(page, box: tuple[float, float, float, float], out_path: Path, dpi: int) -> None:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    clip = fitz.Rect(*box)
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False, annots=False)
    pix.save(out_path)


def extract_assets(
    doc,
    pdf_path: Path,
    out_dir: Path,
    markdown_path: Path,
    dpi: int,
    margin: float,
    debug_captions: bool = False,
    debug_image_blocks: bool = False,
) -> tuple[list[AssetRecord], list[TextBlock]]:
    all_text_blocks = extract_text_blocks(doc)
    captions = detect_captions(all_text_blocks)
    if debug_captions:
        emit_detected_captions(captions)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    assets: list[AssetRecord] = []
    plumber_context = pdfplumber.open(pdf_path) if pdfplumber is not None else nullcontext()
    with plumber_context as plumber_doc:
        for page_index, page in enumerate(doc):
            figure_boxes = collect_visual_boxes(
                page,
                debug_image_blocks=debug_image_blocks,
                page_index=page_index,
            )
            page_blocks = [
                block for block in all_text_blocks if block.page_index == page_index
            ]
            table_boxes = []
            if plumber_doc is not None:
                table_boxes = collect_table_boxes(
                    plumber_doc.pages[page_index],
                    page=page,
                    page_blocks=page_blocks,
                )
            page_captions = [
                caption
                for (caption_page, _), caption in captions.items()
                if caption_page == page_index
            ]
            for caption in page_captions:
                region = choose_region(
                    caption,
                    figure_boxes,
                    table_boxes,
                    page_blocks=page_blocks,
                    page_width=page.rect.width,
                    page_height=page.rect.height,
                )
                if region is None:
                    continue
                if caption.kind == "table":
                    region = refine_table_region(
                        region=region,
                        caption=caption,
                        table_boxes=table_boxes,
                        page_blocks=page_blocks,
                        page_width=page.rect.width,
                        page_height=page.rect.height,
                    )
                else:
                    region = refine_figure_region(
                        region=region,
                        caption=caption,
                        page_blocks=page_blocks,
                        page_width=page.rect.width,
                        page_height=page.rect.height,
                    )
                clipped = clamp_box(region, page.rect, margin=margin)
                clipped = trim_caption_overlap(
                    clipped,
                    caption.bbox,
                    pad=max(2.0, margin / 3.0),
                )
                stem = filename_slug(caption.label, caption.kind)
                filename = f"page-{page_index + 1:03d}-{stem}.png"
                image_path = images_dir / filename
                render_crop(page, clipped, image_path, dpi=dpi)
                rel_link = image_path.relative_to(markdown_path.parent).as_posix()
                assets.append(
                    AssetRecord(
                        page_index=page_index,
                        kind=caption.kind,
                        label=caption.label,
                        caption_text=caption.caption_text,
                        image_path=image_path,
                        rel_link=rel_link,
                        anchor_text=caption.block.text,
                    )
                )
    return assets, all_text_blocks


def heading_level(block: TextBlock, body_size: float) -> int | None:
    text = block.text.strip()
    norm = normalize_text(text)
    if not text or CAPTION_RE.match(text):
        return None

    numbered = HEADING_RE.match(text)
    if numbered:
        return min(6, 2 + numbered.group("num").count("."))

    if norm in KNOWN_SECTION_TITLES:
        return 2

    is_short = len(text) <= 100
    ends_like_heading = not text.endswith((".", "?", "!", ";", ":"))
    if is_short and ends_like_heading and (
        block.max_font_size >= body_size * 1.2 or block.is_bold
    ):
        return 2 if block.max_font_size >= body_size * 1.5 else 3
    return None


def sort_page_blocks(page_blocks: Sequence[TextBlock], page_width: float) -> list[TextBlock]:
    narrow = [block for block in page_blocks if (block.bbox[2] - block.bbox[0]) < page_width * 0.65]
    left = [block for block in narrow if ((block.bbox[0] + block.bbox[2]) / 2.0) < page_width / 2.0]
    right = [block for block in narrow if ((block.bbox[0] + block.bbox[2]) / 2.0) >= page_width / 2.0]

    if len(left) >= 3 and len(right) >= 3:
        first_column_y = min(block.bbox[1] for block in narrow)
        wide = [block for block in page_blocks if block not in narrow]
        header_wide = [block for block in wide if block.bbox[1] <= first_column_y + 4]
        body_wide = [block for block in wide if block not in header_wide]
        ordered = (
            sorted(header_wide, key=lambda block: (block.bbox[1], block.bbox[0]))
            + sorted(left, key=lambda block: (block.bbox[1], block.bbox[0]))
            + sorted(right, key=lambda block: (block.bbox[1], block.bbox[0]))
            + sorted(body_wide, key=lambda block: (block.bbox[1], block.bbox[0]))
        )
        seen: set[tuple[int, tuple[float, float, float, float], str]] = set()
        deduped = []
        for block in ordered:
            key = (block.page_index, block.bbox, block.text)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(block)
        return deduped

    return sorted(page_blocks, key=lambda block: (block.bbox[1], block.bbox[0]))


def render_asset_block(asset: AssetRecord) -> list[str]:
    alt_text = asset.label if asset.label.strip() else asset.kind.title()
    return [
        f"![{alt_text}]({asset.rel_link})",
        f"*{asset.caption_text}*",
        "",
    ]


def build_markdown_from_pdf(doc, blocks: Sequence[TextBlock], assets: Sequence[AssetRecord]) -> str:
    body_size = body_font_size(blocks)
    asset_by_anchor = {
        (asset.page_index, asset.anchor_text): asset for asset in assets
    }
    lines: list[str] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_blocks = [block for block in blocks if block.page_index == page_index]
        for block in sort_page_blocks(page_blocks, page.rect.width):
            asset = asset_by_anchor.get((page_index, block.text))
            if asset is not None:
                lines.extend(render_asset_block(asset))
                continue

            level = heading_level(block, body_size)
            if level is not None:
                lines.append(f"{'#' * level} {block.text.strip()}")
                lines.append("")
            else:
                lines.append(block.text.strip())
                lines.append("")

    lines = [line.rstrip() for line in lines]
    return "\n".join(lines).strip() + "\n"


def caption_similarity(candidate_text: str, caption_text: str) -> float:
    normalized_candidate = normalize_text(candidate_text)
    normalized_caption = normalize_text(caption_text)
    if not normalized_candidate or not normalized_caption:
        return 0.0
    ratio = difflib.SequenceMatcher(None, normalized_candidate, normalized_caption).ratio()
    candidate_tokens = set(normalized_candidate.split())
    caption_tokens = set(normalized_caption.split())
    overlap = len(candidate_tokens & caption_tokens) / max(1, len(caption_tokens))
    bonus = 0.15 if normalized_candidate.startswith(normalized_caption[: min(len(normalized_caption), 12)]) else 0.0
    return 0.65 * ratio + 0.35 * overlap + bonus


def inject_assets_into_skeleton(markdown_text: str, assets: Sequence[AssetRecord]) -> str:
    lines = markdown_text.splitlines()
    used_indices: set[int] = set()
    inserts: dict[int, list[str]] = {}
    unmatched: list[AssetRecord] = []

    for asset in assets:
        best_score = 0.0
        best_start = None
        best_span = 1
        for start in range(len(lines)):
            for span in (1, 2):
                end = start + span
                if end > len(lines):
                    continue
                if any(index in used_indices for index in range(start, end)):
                    continue
                candidate = " ".join(line.strip() for line in lines[start:end] if line.strip())
                if not candidate:
                    continue
                score = caption_similarity(candidate, asset.caption_text)
                if score > best_score:
                    best_score = score
                    best_start = start
                    best_span = span
        if best_start is not None and best_score >= 0.58:
            inserts.setdefault(best_start, []).extend(
                [
                    f"![{asset.label}]({asset.rel_link})",
                    "",
                ]
            )
            for index in range(best_start, best_start + best_span):
                used_indices.add(index)
        else:
            unmatched.append(asset)

    output_lines: list[str] = []
    for index, line in enumerate(lines):
        if index in inserts:
            output_lines.extend(inserts[index])
        output_lines.append(line)

    if unmatched:
        if output_lines and output_lines[-1].strip():
            output_lines.append("")
        output_lines.append("## Extracted Figures And Tables")
        output_lines.append("")
        for asset in unmatched:
            output_lines.extend(render_asset_block(asset))

    return "\n".join(output_lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    require_dependencies()

    pdf_path = Path(args.pdf).expanduser().resolve()
    base_out_dir = Path(args.out_dir).expanduser().resolve()
    markdown_name = validate_markdown_name(args.markdown_name)
    method_dir_name = resolve_method_dir_name(pdf_path, args.method_name)
    out_dir, markdown_path = prepare_method_dir(
        base_out_dir=base_out_dir,
        method_dir_name=method_dir_name,
        markdown_name=markdown_name,
        force_regenerate=args.force_regenerate,
    )

    doc = fitz.open(pdf_path)
    try:
        assets, blocks = extract_assets(
            doc=doc,
            pdf_path=pdf_path,
            out_dir=out_dir,
            markdown_path=markdown_path,
            dpi=args.dpi,
            margin=args.margin,
            debug_captions=args.debug_captions,
            debug_image_blocks=args.debug_image_blocks,
        )

        if args.skeleton_markdown:
            skeleton_path = Path(args.skeleton_markdown).expanduser().resolve()
            skeleton_text = skeleton_path.read_text(encoding="utf-8")
            markdown_text = inject_assets_into_skeleton(skeleton_text, assets)
            mode = "skeleton"
        else:
            markdown_text = build_markdown_from_pdf(doc, blocks, assets)
            mode = "direct"

        markdown_path.write_text(markdown_text, encoding="utf-8")
    finally:
        doc.close()

    run_mode = f"{mode} mode"
    if args.force_regenerate:
        run_mode += ", fresh regenerate"

    print(
        f"Wrote {len(assets)} extracted assets via {run_mode} into "
        f"{out_dir} ({markdown_path}, {out_dir / 'images'})"
    )


if __name__ == "__main__":
    main()
