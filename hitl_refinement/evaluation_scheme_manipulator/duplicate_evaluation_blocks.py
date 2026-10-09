# excel_evaluation_scheme_updater/duplicate_evaluation_blocks.py

from __future__ import annotations

from copy import copy
from pathlib import Path
import openpyxl
from openpyxl.formula.translate import Translator

from utils.default_settings import Default


# ===== Default layout settings =====
DEFAULT_SHEET_NAME = "E4 HITL"
HEADER_ROW = 1
TEMPLATE_START_ROW = 2
TEMPLATE_END_ROW = 6
GAP_ROWS = 1

LABEL_COLUMN = 1  # column A
LABEL_PREFIX = "Turn "
# ================================


from copy import copy


def copy_row_block(
    ws,
    src_start: int,
    src_end: int,
    dst_start: int,
    instruction_text: str = "",
) -> None:
    row_count = src_end - src_start + 1
    row_shift = dst_start - src_start

    # Only copy these column areas:
    copy_areas = [
        (2, 6),   # B:F
        (12, 14), # L:N
    ]

    for offset in range(row_count):
        src_row = src_start + offset
        dst_row = dst_start + offset

        # Copy row height
        ws.row_dimensions[dst_row].height = ws.row_dimensions[src_row].height

        for col_start, col_end in copy_areas:
            for col in range(col_start, col_end + 1):
                src = ws.cell(src_row, col)
                dst = ws.cell(dst_row, col)

                # Copy value with formula translation if needed
                if isinstance(src.value, str) and src.value.startswith("="):
                    dst.value = Translator(src.value, origin=src.coordinate).translate_formula(dst.coordinate)
                else:
                    dst.value = src.value

                # Copy cells styles
                if src.has_style:
                    dst.font = copy(src.font)
                    dst.fill = copy(src.fill)
                    dst.border = copy(src.border)
                    dst.alignment = copy(src.alignment)
                    dst.number_format = src.number_format
                    dst.protection = copy(src.protection)

    # Copy merged cells only if they are fully inside one of the copied areas
    for merged_range in list(ws.merged_cells.ranges):
        min_col, min_row, max_col, max_row = merged_range.bounds

        in_row_block = src_start <= min_row and max_row <= src_end
        in_copy_area = any(
            col_start <= min_col and max_col <= col_end
            for col_start, col_end in copy_areas
        )

        if in_row_block and in_copy_area:
            ws.merge_cells(
                start_row=min_row + row_shift,
                start_column=min_col,
                end_row=max_row + row_shift,
                end_column=max_col,
            )

    # Write instruction text into 'Notes' column (R) on the first row of the new block
    if instruction_text:
        ws.cell(dst_start, 18).value = instruction_text   # column R = 18


def set_block_label(ws, first_row: int, block_index: int) -> None:
    ws.cell(first_row, LABEL_COLUMN).value = f"{LABEL_PREFIX}{block_index}"


def ensure_evaluation_blocks(
    workbook_path: str | Path,
    total_blocks: int,
    instruction_text: str | None = None,
    *,
    sheet_name: str = DEFAULT_SHEET_NAME,
    template_start_row: int = TEMPLATE_START_ROW,
    template_end_row: int = TEMPLATE_END_ROW,
    gap_rows: int = GAP_ROWS,
) -> Path:
    """
    Ensure the workbook contains exactly the required number of HITL blocks,
    counting the existing template block as HITL 0.

    Example:
        total_blocks=1 -> only HITL 0
        total_blocks=2 -> HITL 0 and HITL 1
        total_blocks=3 -> HITL 0, HITL 1, HITL 2
    """
    workbook_path = Path(workbook_path)
    if not workbook_path.exists():
        raise FileNotFoundError(f"Evaluation workbook not found:\n{workbook_path}")

    wb = openpyxl.load_workbook(workbook_path)
    ws = wb[sheet_name]

    block_rows = template_end_row - template_start_row + 1

    # Always relabel the template block as HITL 0
    set_block_label(ws, template_start_row, 0)

    # Count how many blocks already exist by checking label positions
    existing_blocks = 1
    while True:
        candidate_row = template_start_row + existing_blocks * (block_rows + gap_rows)
        value = ws.cell(candidate_row, LABEL_COLUMN).value
        if value == f"{LABEL_PREFIX}{existing_blocks}":
            existing_blocks += 1
        else:
            break

    # Add only the missing blocks
    for block_index in range(existing_blocks, total_blocks):
        dst_start = template_start_row + block_index * (block_rows + gap_rows)
        copy_row_block(ws, template_start_row, template_end_row, dst_start, instruction_text)
        set_block_label(ws, dst_start, block_index)

    wb.save(workbook_path)
    return workbook_path


def trim_evaluation_blocks(
    session_paths: dict[str, Path],
    turn_index: int,
    *,
    workbook_name: str | Path = Default.WORKBOOK_NAME,
    sheet_name: str = DEFAULT_SHEET_NAME,
    template_start_row: int = TEMPLATE_START_ROW,
    template_end_row: int = TEMPLATE_END_ROW,
    gap_rows: int = GAP_ROWS,
) -> Path | None:
    """
    Remove any HITL blocks beyond the required number, keeping only the first total_blocks blocks.
    """
    workbook_path = session_paths["evaluations"] / workbook_name

    if not workbook_path.exists():
        print(f"\n[WARNING] Evaluation workbook not found, skipping trimming:\n{workbook_path}\n")
        # raise FileNotFoundError(f"Evaluation workbook not found:\n{workbook_path}")
        return None

    total_blocks = turn_index + 1

    wb = openpyxl.load_workbook(workbook_path)
    ws = wb[sheet_name]

    block_rows = template_end_row - template_start_row + 1
    span = block_rows + gap_rows

    # First row after the last block we want to keep
    cutoff_row = template_start_row + total_blocks * span

    max_row = ws.max_row
    if cutoff_row <= max_row:
        ws.delete_rows(cutoff_row, max_row - cutoff_row + 1)

    wb.save(workbook_path)
    return workbook_path