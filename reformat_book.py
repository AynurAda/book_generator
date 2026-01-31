"""Quick script to reformat existing book with new header hierarchy."""

import re
import os
from book_generator.pdf import generate_pdf

OUTPUT_DIR = "output/20260131_190723"

# Read existing book
book_path = os.path.join(OUTPUT_DIR, "06_full_book.txt")
with open(book_path, "r") as f:
    content = f.read()

# Transform headers (order matters - do most specific first)
# #### 1.1.1 -> ### 1.1.1 (subsections -> sections)
content = re.sub(r'^#### (\d+\.\d+\.\d+)', r'### \1', content, flags=re.MULTILINE)

# ### 1.1 -> ## 1.1 (sections -> chapters)
content = re.sub(r'^### (\d+\.\d+\s)', r'## \1', content, flags=re.MULTILINE)

# ## 1. -> # 1. (chapters -> parts)
content = re.sub(r'^## (\d+\.)', r'# \1', content, flags=re.MULTILINE)

# ## Introduction -> # Introduction
content = re.sub(r'^## Introduction', r'# Introduction', content, flags=re.MULTILINE)

# ## About the Author -> # About the Author
content = re.sub(r'^## About the Author', r'# About the Author', content, flags=re.MULTILINE)

# Save reformatted book
new_book_path = os.path.join(OUTPUT_DIR, "06_full_book_reformatted.txt")
with open(new_book_path, "w") as f:
    f.write(content)

print(f"Saved reformatted book to {new_book_path}")

# Generate new PDF
pdf_path = os.path.join(OUTPUT_DIR, "06_full_book_reformatted.pdf")
cover_path = os.path.join(OUTPUT_DIR, "book_cover.png")

# Get book name from topic file
topic_path = os.path.join(OUTPUT_DIR, "00_topic.txt")
with open(topic_path, "r") as f:
    for line in f:
        if line.startswith("Book Name:"):
            book_name = line.split(":", 1)[1].strip()
            break

generate_pdf(
    content,
    book_name,
    pdf_path,
    cover_path=cover_path if os.path.exists(cover_path) else None,
    base_url=OUTPUT_DIR
)

print(f"Generated PDF: {pdf_path}")
