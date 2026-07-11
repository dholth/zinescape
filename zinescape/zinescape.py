"""
Generate an inkscape template to author a zine, or compile a multi-page document
into a zine.
"""

import argparse
import xml.etree.ElementTree as ET

from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

# A4_WIDTH = 595.28  # A4 width in points
# A4_HEIGHT = 841.89  # A4 height in points

LETTER_WIDTH = 612
LETTER_HEIGHT = 792


def template(f_name, n_pages, width, height):

    width *= 96
    height *= 96  # 8.5
    spacing = 96  # 1.0
    margin = 48  # 0.5

    doc = f"""<?xml version='1.0' encoding='utf-8'?>
<svg xmlns="http://www.w3.org/2000/svg"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    width="{width}"
    height="{height}"
    viewBox="0 0 528 816"
    version="1.1"
    id="svg5"
    inkscape:version="1.2.2 (b0a8486541, 2022-12-01)"
    xml:space="preserve">
    <defs id="defs21" />
    <sodipodi:namedview id="namedview7" pagecolor="#ffffff" bordercolor="#666666" borderopacity="1.0" inkscape:pageshadow="2" inkscape:pageopacity="0.0" inkscape:pagecheckerboard="0" inkscape:document-units="in" inkscape:snap-global="false" fit-margin-top="0" fit-margin-left="0" fit-margin-right="0" fit-margin-bottom="0" units="in" width="528in" inkscape:showpageshadow="2" inkscape:deskcolor="#d1d1d1" showguides="false" inkscape:lockguides="false">
    <inkscape:grid type="xygrid" id="grid1046" originx="0" originy="0" spacingy="1" spacingx="1" units="in" visible="false" />
    """

    tail = """
    </sodipodi:namedview>
</svg>"""

    pages = []
    for i in range(n_pages):
        if i == n_pages - 1:
            x = -width
        else:
            x = (i) * width + ((i / 2) + (i % 2) / 2) * spacing
        y = 0
        width = width
        margin = margin

        pages.append(
            f"""<inkscape:page x="{x}" y="{y}" width="{width}" height="{height}" id="page_{i}" margin="{margin}" bleed="0" />"""
        )

    doc = doc + "\n".join(pages) + tail

    # nice XML rendering instead of ns0:tag, ns1:tag etc.
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    ET.register_namespace(
        "sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    )
    root = ET.fromstring(doc)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(f_name, encoding="utf-8", xml_declaration=True)


def nup(input_pdf_path, output_pdf_path, rows=1, cols=2):
    is_landscape = True
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    num_pages = len(reader.pages)
    pages_per_sheet = rows * cols

    booklet_indices = []
    for i in range(int(len(reader.pages) / 4)):
        booklet_indices.append(i * 2)
        booklet_indices.append(len(reader.pages) - i * 2 - 1)
        booklet_indices.append(i * 2 + 1)
        booklet_indices.append(len(reader.pages) - i * 2 - 2)

    if is_landscape:
        width = LETTER_HEIGHT
        height = LETTER_WIDTH
    else:
        width = LETTER_WIDTH
        height = LETTER_HEIGHT

    for i in range(0, num_pages, pages_per_sheet):
        new_page = writer.add_blank_page(width=width, height=height)

        page_width = width / cols
        page_height = height / rows

        positions = [
            (col * page_width, (rows - 1 - row) * page_height)
            for row in range(rows)
            for col in range(cols)
        ]

        for j in range(pages_per_sheet):
            if i + j < num_pages:
                page = reader.pages[booklet_indices[i + j]]

                # Calculate the scale factor to maintain aspect ratio
                scale_x = page_width / page.mediabox.width
                scale_y = page_height / page.mediabox.height
                scale = min(scale_x, scale_y)  # Use the smaller scale to ensure it fits

                page.scale_by(scale)

                if i % 4 >= 2:
                    # Adjust the positions to center the page horizontally and vertically
                    x_offset = (page_width - page.mediabox.width) / 2
                    y_offset = (page_height - page.mediabox.height) / 2

                    # Translate the page to the correct position
                    position = positions[j]
                    translation_matrix = [
                        1,
                        0,
                        0,
                        1,
                        position[0] + x_offset,
                        position[1] + y_offset,
                    ]
                    page.mediabox = RectangleObject([0, 0, page_width, page_height])
                    new_page.merge_transformed_page(page, translation_matrix)
                else:
                    # Adjust the positions to center the page horizontally and vertically
                    x_offset = (page_width - page.mediabox.width) / 2
                    y_offset = (page_height - page.mediabox.height) / 2

                    # Translate the page to the correct position
                    position = positions[j]
                    translation_matrix = [
                        -1,
                        0,
                        0,
                        -1,
                        page_width + position[0] + x_offset,
                        page_height + position[1] + y_offset,
                    ]
                    page.mediabox = RectangleObject([0, 0, page_width, page_height])
                    new_page.merge_transformed_page(page, translation_matrix)

    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)


def cli():
    parser = argparse.ArgumentParser(
        prog="zinescape", description="Utilities for making zines", epilog="epilog here"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile command
    compile_parser = subparsers.add_parser(
        "compile", help="Compile PDF pages into a booklet"
    )
    compile_parser.add_argument("filename", help="Input PDF file")
    compile_parser.add_argument("out_fn", nargs="?", help="Output PDF file (optional)")
    compile_parser.add_argument(
        "-R", "--rows", type=int, default=1, help="Number of rows (default: 1)"
    )
    compile_parser.add_argument(
        "-C", "--cols", type=int, default=2, help="Number of columns (default: 2)"
    )

    # template command
    template_parser = subparsers.add_parser(
        "template", help="Create a template SVG file"
    )
    template_parser.add_argument("filename", help="Output template filename")
    template_parser.add_argument(
        "-N", "--n_pages", type=int, required=True, help="Number of pages in template"
    )
    template_parser.add_argument(
        "-W", "--width", type=float, default=5.5, help="Width in inches (default: 5.5)"
    )
    template_parser.add_argument(
        "-H",
        "--height",
        type=float,
        default=8.5,
        help="Height in inches (default: 8.5)",
    )

    args = parser.parse_args()

    if args.command == "compile":
        out_fn = args.out_fn
        if out_fn is None:
            parts = args.filename.split(".")
            if len(parts) > 1:
                out_fn = f"{parts[0]}.compiled.{parts[1]}"
            else:
                out_fn = f"{args.filename}.compiled"
        nup(args.filename, out_fn, args.rows, args.cols)
    elif args.command == "template":
        template(args.filename, args.n_pages, args.width, args.height)

    else:
        parser.print_help()
