"""
Document downloading and processing for citation verification.

Handles downloading PDFs/web pages and chunking them into
passages for semantic search and verification.
"""

import logging
import hashlib
import os
import re
from typing import List, Optional
import urllib.request
import urllib.error

from .models import Source, Passage

logger = logging.getLogger(__name__)

# Chunk settings
DEFAULT_CHUNK_SIZE = 500  # words
DEFAULT_CHUNK_OVERLAP = 50  # words


async def download_source(source: Source, output_dir: str) -> Optional[str]:
    """
    Download a source document (PDF or web page).

    Args:
        source: Source object with URL
        output_dir: Directory to save downloaded files

    Returns:
        Path to downloaded file, or None if download fails
    """
    url = source.url
    source_id = source.id

    # Create sources directory
    sources_dir = os.path.join(output_dir, "sources")
    os.makedirs(sources_dir, exist_ok=True)

    # Determine file extension
    if ".pdf" in url.lower():
        ext = ".pdf"
    else:
        ext = ".html"

    output_path = os.path.join(sources_dir, f"{source_id}{ext}")

    # Skip if already downloaded
    if os.path.exists(output_path):
        logger.info(f"Source already downloaded: {source_id}")
        return output_path

    try:
        logger.info(f"Downloading source: {url[:60]}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BookGenerator/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()

            with open(output_path, 'wb') as f:
                f.write(content)

        logger.info(f"Downloaded: {output_path}")
        return output_path

    except urllib.error.HTTPError as e:
        logger.warning(f"HTTP error downloading {url}: {e.code}")
        return None
    except urllib.error.URLError as e:
        logger.warning(f"URL error downloading {url}: {e.reason}")
        return None
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return None


def extract_text_from_pdf(pdf_path: str) -> List[dict]:
    """
    Extract text from a PDF file with page numbers.

    Args:
        pdf_path: Path to PDF file

    Returns:
        List of dicts with 'text' and 'page' keys
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed. Cannot extract PDF text.")
        return []

    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                pages.append({
                    "text": text.strip(),
                    "page": page_num
                })
        doc.close()
    except Exception as e:
        logger.warning(f"Failed to extract PDF text: {e}")

    return pages


def extract_text_from_html(html_path: str) -> List[dict]:
    """
    Extract main content text from an HTML file.

    Args:
        html_path: Path to HTML file

    Returns:
        List of dicts with 'text' and 'page' (always 1 for HTML)
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("BeautifulSoup not installed. Cannot extract HTML text.")
        return []

    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Try to find main content
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if main:
            text = main.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        if text.strip():
            return [{"text": text.strip(), "page": 1}]

    except Exception as e:
        logger.warning(f"Failed to extract HTML text: {e}")

    return []


def chunk_text(
    text: str,
    page_number: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[dict]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        page_number: Page number for reference
        chunk_size: Target chunk size in words
        overlap: Overlap between chunks in words

    Returns:
        List of chunk dicts with 'text', 'page', 'start_word', 'end_word'
    """
    # Split into words while preserving some structure
    words = text.split()

    if len(words) <= chunk_size:
        return [{
            "text": text,
            "page": page_number,
            "start_word": 0,
            "end_word": len(words)
        }]

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))

        # Try to end at a sentence boundary
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        # Look for sentence end near the boundary
        if end < len(words):
            last_period = chunk_text.rfind('. ')
            last_question = chunk_text.rfind('? ')
            last_exclaim = chunk_text.rfind('! ')
            last_sentence = max(last_period, last_question, last_exclaim)

            if last_sentence > len(chunk_text) * 0.7:  # Only if we keep 70%+
                chunk_text = chunk_text[:last_sentence + 1]
                # Recalculate end based on actual words used
                actual_words = len(chunk_text.split())
                end = start + actual_words

        chunks.append({
            "text": chunk_text.strip(),
            "page": page_number,
            "start_word": start,
            "end_word": end
        })

        # Move start with overlap
        start = end - overlap
        if start >= len(words) - overlap:
            break

    return chunks


async def process_source_to_passages(
    source: Source,
    output_dir: str,
) -> List[Passage]:
    """
    Download and process a source into passages.

    Args:
        source: Source to process
        output_dir: Directory for downloads

    Returns:
        List of Passage objects
    """
    # Download the source
    file_path = await download_source(source, output_dir)
    if not file_path:
        return []

    # Update source with path
    source.pdf_path = file_path

    # Extract text based on file type
    if file_path.endswith('.pdf'):
        pages = extract_text_from_pdf(file_path)
    else:
        pages = extract_text_from_html(file_path)

    if not pages:
        logger.warning(f"No text extracted from source: {source.id}")
        return []

    # Chunk each page
    passages = []
    chunk_index = 0

    for page_data in pages:
        chunks = chunk_text(
            text=page_data["text"],
            page_number=page_data["page"],
        )

        for chunk in chunks:
            passage = Passage(
                id=f"{source.id}_c{chunk_index}",
                content=chunk["text"],
                source_id=source.id,
                page_number=chunk["page"],
            )
            passages.append(passage)
            chunk_index += 1

    logger.info(f"Created {len(passages)} passages from source {source.id}")
    return passages


def compute_content_hash(text: str) -> str:
    """Compute hash of text content for deduplication."""
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()
