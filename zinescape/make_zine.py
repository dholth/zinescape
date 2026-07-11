from pypdf import PdfReader, PdfWriter


def create_zine(input_pdf_path: str, output_pdf_path: str) -> None:
    """
    Creates a zine layout from an input PDF.

    The output is a single landscape Letter-sized page (11x8.5 inches)
    containing 8 pages from the input PDF, arranged in a 4x2 grid.

    Layout Specification:
    - Row 1 (Top): Pages 5, 4, 3, 2 (rotated 180 degrees)
    - Row 2 (Bottom): Pages 6, 7, 8, 1 (right-side up)
    """
    try:
        reader = PdfReader(input_pdf_path)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    writer = PdfWriter()

    # Landscape Letter size in points (1 inch = 72 points)
    WIDTH = 11 * 72
    HEIGHT = 8.5 * 72
    zine_page = writer.add_blank_page(width=WIDTH, height=HEIGHT)

    # Grid dimensions
    CELL_W = WIDTH / 4
    CELL_H = HEIGHT / 2

    # Layout mapping: (source_page_index, col, row_idx, is_upside_down)
    # row_idx 0 is the top row, row_idx 1 is the bottom row.
    # Coordinates (0,0) are at the bottom-left of the page.
    layout = [
        # Top Row (y-offset = HEIGHT - CELL_H)
        (4, 0, 0, True),  # Page 5
        (3, 1, 0, True),  # Page 4
        (2, 2, 0, True),  # Page 3
        (1, 3, 0, True),  # Page 2
        # Bottom Row (y-offset = 0)
        (5, 0, 1, False),  # Page 6
        (6, 1, 1, False),  # Page 7
        (7, 2, 1, False),  # Page 8
        (0, 3, 1, False),  # Page 1
    ]

    for page_idx, col, row_idx, upside_down in layout:
        if page_idx >= len(reader.pages):
            print(
                f"Warning: Page {page_idx + 1} not found in {input_pdf_path}. Skipping."
            )
            continue

        page = reader.pages[page_idx]

        # Calculate target position (bottom-left of the cell)
        tx = col * CELL_W
        ty = (HEIGHT - CELL_H) if row_idx == 0 else 0

        # Scale page to fit the cell exactly
        page.scale_to(CELL_W, CELL_H)

        # Apply rotation if specified
        if upside_down:
            page.rotate(180)
            page.transfer_rotation_to_content()

        # Place the transformed page into the zine page
        zine_page.merge_translated_page(page, tx, ty)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)
    print(f"Successfully created {output_pdf_path}")


if __name__ == "__main__":
    create_zine("output.pdf", "book.pdf")
