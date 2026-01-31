"""
PDF generation for the final book.

This module handles conversion of the book content to a professionally
styled PDF with cover page, table of contents, and proper typography.
"""

import os
import re
import base64
import logging
import subprocess
import tempfile
import urllib.request
import urllib.parse
from typing import Optional

import markdown
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)


def process_latex_math(content: str) -> str:
    """
    Convert LaTeX math notation to MathML for PDF rendering.

    Handles:
    - Display math: $$...$$ or \[...\]
    - Inline math: $...$ or \(...\)
    - Escaped parentheses with math: (\mathbb{...})

    Returns:
        Content with LaTeX converted to MathML
    """
    try:
        import latex2mathml.converter
        has_latex2mathml = True
    except ImportError:
        logger.warning("latex2mathml not installed - math formulas will show as text")
        has_latex2mathml = False
        return content

    def latex_to_mathml(latex_code: str, display: bool = False) -> str:
        """Convert a single LaTeX expression to MathML."""
        try:
            mathml = latex2mathml.converter.convert(latex_code)
            if display:
                # Wrap display math in a centered div
                return f'<div class="math-display">{mathml}</div>'
            else:
                return f'<span class="math-inline">{mathml}</span>'
        except Exception as e:
            logger.warning(f"Failed to convert LaTeX: {latex_code[:50]}... - {e}")
            # Return formatted code block as fallback
            return f'<code class="math-fallback">{latex_code}</code>'

    # Pattern for display math: $$...$$ or \[...\]
    display_pattern1 = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
    display_pattern2 = re.compile(r'\\\[(.+?)\\\]', re.DOTALL)

    # Pattern for inline math: $...$ (not $$)
    inline_pattern1 = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)')

    # Pattern for \(...\)
    inline_pattern2 = re.compile(r'\\\((.+?)\\\)')

    # Pattern for (\mathbb{...}) style - common malformed LaTeX
    paren_math_pattern = re.compile(r'\(\\(math[a-z]*\{[^}]+\}[^)]*)\)')

    # Process display math first (to avoid conflicts with inline)
    def replace_display(match):
        return latex_to_mathml(match.group(1).strip(), display=True)

    content = display_pattern1.sub(replace_display, content)
    content = display_pattern2.sub(replace_display, content)

    # Process inline math
    def replace_inline(match):
        return latex_to_mathml(match.group(1).strip(), display=False)

    content = inline_pattern1.sub(replace_inline, content)
    content = inline_pattern2.sub(replace_inline, content)

    # Process parenthesized math expressions like (\mathbb{R}^d)
    def replace_paren_math(match):
        return latex_to_mathml(match.group(1).strip(), display=False)

    content = paren_math_pattern.sub(replace_paren_math, content)

    # Also catch standalone \mathbf, \mathbb, etc. that might be outside delimiters
    standalone_math = re.compile(r'\\(math(?:bf|bb|cal|rm|it|sf|tt|frak)\{[^}]+\})')

    def replace_standalone(match):
        return latex_to_mathml(match.group(0), display=False)

    content = standalone_math.sub(replace_standalone, content)

    return content


def render_mermaid_to_image(mermaid_code: str, output_path: str, use_cli: bool = True) -> Optional[str]:
    """
    Render Mermaid code to an image file.

    Tries mermaid-cli first, falls back to mermaid.ink API.

    Args:
        mermaid_code: The Mermaid diagram code
        output_path: Path to save the rendered image (PNG)
        use_cli: Whether to try mermaid-cli first

    Returns:
        Path to the rendered image, or None if rendering failed
    """
    # Try mermaid-cli (mmdc) first if available
    if use_cli:
        try:
            # Create a temp file for the mermaid code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
                f.write(mermaid_code)
                mmd_path = f.name

            # Run mmdc
            result = subprocess.run(
                ['mmdc', '-i', mmd_path, '-o', output_path, '-b', 'transparent'],
                capture_output=True,
                timeout=30
            )

            os.unlink(mmd_path)

            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Rendered Mermaid diagram with CLI: {output_path}")
                return output_path
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            logger.debug(f"mermaid-cli not available: {e}")

    # Fall back to mermaid.ink API
    try:
        # Encode the mermaid code for the API
        encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=white"

        # Download the image
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'BookGenerator/1.0'}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Rendered Mermaid diagram with API: {output_path}")
            return output_path

    except Exception as e:
        logger.warning(f"Mermaid API rendering failed: {e}")

    return None


def process_mermaid_blocks(content: str, output_dir: str) -> str:
    """
    Find and render all Mermaid code blocks in the content.

    Replaces ```mermaid ... ``` blocks with image references.

    Args:
        content: The markdown content
        output_dir: Directory to save rendered images

    Returns:
        Content with Mermaid blocks replaced by images
    """
    # Pattern to match mermaid code blocks
    mermaid_pattern = re.compile(
        r'```mermaid\s*\n(.*?)```',
        re.DOTALL | re.IGNORECASE
    )

    diagram_counter = 0

    def replace_mermaid(match):
        nonlocal diagram_counter
        diagram_counter += 1

        mermaid_code = match.group(1).strip()
        image_filename = f"mermaid_diagram_{diagram_counter:03d}.png"
        image_path = os.path.join(output_dir, image_filename)

        # Render the diagram
        rendered_path = render_mermaid_to_image(mermaid_code, image_path)

        if rendered_path:
            # Return an image reference
            return f'\n\n<div class="mermaid-diagram"><img src="{image_filename}" alt="Diagram {diagram_counter}"></div>\n\n'
        else:
            # If rendering failed, remove the diagram entirely
            logger.warning(f"Failed to render Mermaid diagram {diagram_counter} - removing from output")
            return '\n\n'  # Just remove it, don't show raw code

    processed_content = mermaid_pattern.sub(replace_mermaid, content)

    if diagram_counter > 0:
        logger.info(f"Processed {diagram_counter} Mermaid diagrams")

    return processed_content

# CSS stylesheet for the book
BOOK_CSS = '''
@page {
    size: A4;
    margin: 2.5cm 2cm;
    @top-center {
        content: string(chapter-title);
        font-size: 9pt;
        color: #888;
        font-style: italic;
    }
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #888;
    }
}
@page :first {
    margin: 0;
    @top-center { content: none; }
    @bottom-center { content: none; }
}
@page part {
    @top-center { content: none; }
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
    font-family: 'Palatino Linotype', Palatino, Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #222;
    text-align: justify;
    hyphens: auto;
}
/* Part titles (h1) - new page, styled header */
h1 {
    page: part;
    page-break-before: always;
    font-size: 26pt;
    font-weight: bold;
    text-align: left;
    border-bottom: 3px solid #333;
    margin-top: 0;
    margin-bottom: 1.5em;
    padding-top: 1em;
    padding-bottom: 0.5em;
    color: #1a1a1a;
}
/* Chapter titles (h2) */
h2 {
    string-set: chapter-title content();
    font-size: 18pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 2em;
    margin-bottom: 1em;
    page-break-before: always;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.5em;
}
/* Section titles (h3) */
h3 {
    font-size: 13pt;
    font-weight: bold;
    color: #333;
    margin-top: 2em;
    margin-bottom: 0.8em;
    border-left: 4px solid #666;
    padding-left: 0.8em;
}
/* Subsection titles (h4) - for internal structure */
h4 {
    font-size: 11pt;
    font-weight: bold;
    color: #444;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
p {
    margin-bottom: 0.8em;
    text-indent: 1.5em;
}
p:first-of-type, h1 + p, h2 + p, h3 + p, h4 + p, hr + p, blockquote + p {
    text-indent: 0;
}
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2.5em 0;
}
em {
    font-style: italic;
}
strong {
    font-weight: bold;
}
blockquote {
    margin: 1.5em 2em;
    padding: 0.5em 1em;
    border-left: 3px solid #999;
    font-style: italic;
    color: #555;
    background: #fafafa;
}
code {
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 9.5pt;
    background: #f4f4f4;
    padding: 0.15em 0.4em;
    border-radius: 3px;
    border: 1px solid #e0e0e0;
}
pre {
    background: #f8f8f8;
    padding: 1em 1.2em;
    overflow-x: auto;
    font-size: 9pt;
    border-radius: 4px;
    margin: 1.2em 0;
    border: 1px solid #e0e0e0;
    line-height: 1.5;
}
pre code {
    background: none;
    border: none;
    padding: 0;
}
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}
li {
    margin-bottom: 0.4em;
}
li > ul, li > ol {
    margin-top: 0.3em;
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
    padding-top: 0;
    page-break-before: avoid;
    page-break-after: avoid;
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
    margin-bottom: 2em;
    font-size: 20pt;
    page-break-before: avoid;
    border-bottom: none;
    font-variant: small-caps;
    letter-spacing: 0.05em;
}
.toc-columns {
    column-count: 2;
    column-gap: 2.5em;
}
.toc-columns p {
    text-indent: 0;
    margin-bottom: 0.6em;
    break-inside: avoid;
    font-size: 9.5pt;
    line-height: 1.5;
}
.toc-columns strong {
    font-size: 10.5pt;
}
.mermaid-diagram {
    text-align: center;
    margin: 2em 0;
    page-break-inside: avoid;
}
.mermaid-diagram img {
    max-width: 90%;
    height: auto;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1em;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.mermaid-code {
    margin: 1.5em 0;
    text-align: center;
}
.mermaid-code pre {
    text-align: left;
    display: inline-block;
    max-width: 90%;
}
.mermaid-error {
    color: #999;
    font-size: 9pt;
}
.figure {
    text-align: center;
    margin: 2em 0;
    page-break-inside: avoid;
}
.figure img {
    max-width: 90%;
    height: auto;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.figure figcaption, .mermaid-diagram + p em, .figure + p em {
    font-size: 9pt;
    color: #666;
    font-style: italic;
    margin-top: 0.8em;
    display: block;
    text-align: center;
    text-indent: 0;
}
.math-display {
    text-align: center;
    margin: 1.2em 0;
    overflow-x: auto;
}
.math-display math {
    font-size: 12pt;
}
.math-inline math {
    font-size: inherit;
    vertical-align: middle;
}
.math-fallback {
    font-family: 'Consolas', 'Courier New', monospace;
    background: #f5f5f5;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 9.5pt;
}
math {
    font-family: 'STIX Two Math', 'Cambria Math', 'Latin Modern Math', serif;
}
/* First paragraph after part/chapter - drop cap style indent */
h1 + p:first-letter, h2 + p:first-letter {
    font-size: 1.1em;
    font-weight: bold;
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

    # Process LaTeX math - convert to MathML
    processed_content = process_latex_math(book_content)

    # Process Mermaid diagrams - render to images
    if base_url:
        processed_content = process_mermaid_blocks(processed_content, base_url)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'toc', 'smarty'])
    html_content = md.convert(processed_content)

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
