"""
PDF generation for the final book.

This module handles conversion of the book content to a professionally
styled PDF with cover page, table of contents, and proper typography.
"""

import os
import logging
from typing import Optional

import markdown
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

# CSS stylesheet for the book
BOOK_CSS = '''
@page {
    size: A4;
    margin: 2.5cm 2cm;
    @top-center {
        content: string(book-title);
        font-size: 10pt;
        color: #666;
    }
    @bottom-center {
        content: counter(page);
        font-size: 10pt;
    }
}
@page :first {
    margin: 0;
    @top-center { content: none; }
    @bottom-center { content: none; }
}
.cover-page {
    page-break-after: always;
    margin: 0;
    padding: 0;
    text-align: center;
}
.cover-image {
    width: 100%;
    height: 100vh;
    object-fit: contain;
}
body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    text-align: justify;
    hyphens: auto;
}
h1 {
    font-size: 32pt;
    text-align: center;
    border-bottom: none;
    margin-top: 3em;
}
h2 {
    string-set: book-title content();
    font-size: 18pt;
    color: #1a1a1a;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    page-break-before: always;
    border-bottom: 2px solid #333;
    padding-bottom: 0.3em;
}
h3 {
    font-size: 13pt;
    color: #3a3a3a;
    margin-top: 1.2em;
}
p {
    margin-bottom: 0.8em;
    text-indent: 1.5em;
}
p:first-of-type, h1 + p, h2 + p, h3 + p, hr + p {
    text-indent: 0;
}
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 2em 0;
}
em {
    font-style: italic;
}
strong {
    font-weight: bold;
}
blockquote {
    margin: 1em 2em;
    padding-left: 1em;
    border-left: 3px solid #ccc;
    font-style: italic;
    color: #555;
}
code {
    font-family: 'Courier New', monospace;
    font-size: 10pt;
    background: #f5f5f5;
    padding: 0.2em 0.4em;
    border-radius: 3px;
}
pre {
    background: #f5f5f5;
    padding: 1em;
    overflow-x: auto;
    font-size: 9pt;
    border-radius: 5px;
    margin: 1em 0;
}
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}
li {
    margin-bottom: 0.3em;
}
.title-page {
    text-align: center;
    padding-top: 30%;
}
.title-page h1 {
    font-size: 36pt;
    border: none;
    margin: 0;
    page-break-before: avoid;
}
.title-page .subtitle {
    font-size: 14pt;
    color: #666;
    margin-top: 1em;
}
.toc {
    page-break-before: always;
    page-break-after: always;
}
.toc h2 {
    text-align: center;
    margin-bottom: 1.5em;
    font-size: 20pt;
    page-break-before: avoid;
    border-bottom: none;
}
.toc-columns {
    column-count: 2;
    column-gap: 2em;
}
.toc-columns p {
    text-indent: 0;
    margin-bottom: 0.8em;
    break-inside: avoid;
    font-size: 10pt;
    line-height: 1.4;
}
.toc-columns strong {
    font-size: 11pt;
}
'''


def generate_pdf(
    book_content: str,
    book_name: str,
    output_path: str,
    cover_path: Optional[str] = None,
    base_url: Optional[str] = None
) -> str:
    """
    Generate a PDF from the book content.

    Args:
        book_content: The markdown content of the book
        book_name: The book's title
        output_path: Path to save the PDF
        cover_path: Optional path to cover image
        base_url: Base URL for resolving relative paths (typically the output directory)

    Returns:
        The path to the generated PDF
    """
    logger.info("Generating PDF...")

    css = CSS(string=BOOK_CSS)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'toc', 'smarty'])
    html_content = md.convert(book_content)

    # Add cover page if cover image exists
    cover_html = ""
    if cover_path and os.path.exists(cover_path):
        cover_filename = os.path.basename(cover_path)
        cover_html = f'''<div class="cover-page">
<img src="{cover_filename}" alt="Book Cover" class="cover-image">
</div>
'''

    # Wrap in full HTML document
    full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{book_name}</title>
</head>
<body>
{cover_html}{html_content}
</body>
</html>'''

    # Generate PDF
    html_doc = HTML(string=full_html, base_url=base_url)
    html_doc.write_pdf(output_path, stylesheets=[css])

    logger.info(f"PDF saved: {output_path}")
    return output_path
