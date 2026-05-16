#!/usr/bin/env python3
"""
ebook2txt — Convert EPUB and PDF to plain text for Altoid eInk Reader
=====================================================================

Usage:
    python3 ebook2txt.py book.epub          → book.txt
    python3 ebook2txt.py book.pdf           → book.txt
    python3 ebook2txt.py book.epub -o out.txt
    python3 ebook2txt.py book.pdf -w 60     → wrap at 60 chars

Output is clean UTF-8 plain text with:
  • Chapter titles preserved (## markers)
  • Paragraph breaks (double newline)
  • Optional hard-wrap to a specific line width
  • Stripped images, formatting, metadata
"""

import argparse
import html.parser
import io
import os
import re
import sys
import zipfile
from pathlib import Path


# ── EPUB Converter ──────────────────────────────────────────────

class EPUBTextExtractor(html.parser.HTMLParser):
    """Extract readable text from XHTML, preserving paragraph breaks."""

    BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'li', 'br', 'hr', 'title', 'section', 'article',
                  'header', 'footer', 'blockquote', 'pre', 'tr'}
    SKIP_TAGS = {'script', 'style', 'head', 'nav', 'svg', 'img',
                 'figure', 'figcaption', 'picture', 'video', 'audio'}

    def __init__(self):
        super().__init__()
        self.text = ''
        self._skip = 0
        self._last_was_newline = False
        self._h_tag = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._h_tag = True
        if tag in self.BLOCK_TAGS and not self._last_was_newline:
            self.text += '\n'
            self._last_was_newline = True

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip > 0:
            self._skip -= 1
        if tag in self.BLOCK_TAGS:
            if tag == 'br':
                self.text += '\n'
            elif not self._last_was_newline:
                self.text += '\n'
                self._last_was_newline = True
            if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                self.text += '\n'
                self._h_tag = False

    def handle_data(self, data):
        if self._skip > 0:
            return
        text = data.strip()
        if not text:
            return
        if self._h_tag:
            self.text += '## ' + text + '\n\n'
            self._last_was_newline = True
        else:
            self.text += text + ' '
            self._last_was_newline = False

    def handle_entityref(self, name):
        if name == 'nbsp':
            self.handle_data(' ')
        elif name == 'amp':
            self.handle_data('&')
        elif name == 'lt':
            self.handle_data('<')
        elif name == 'gt':
            self.handle_data('>')
        elif name == 'quot':
            self.handle_data('"')
        elif name == 'apos':
            self.handle_data("'")


def epub_to_text(epub_path):
    """Extract text from an EPUB file. Returns (title, text)."""
    title = Path(epub_path).stem
    chapters = []

    with zipfile.ZipFile(epub_path, 'r') as zf:
        # Find content files (XHTML/HTML)
        content_files = sorted(
            [f for f in zf.namelist()
             if f.lower().endswith(('.xhtml', '.html', '.htm'))
             and not 'nav' in f.lower()
             and not 'toc' in f.lower()],
            key=lambda f: f.lower()
        )

        if not content_files:
            raise ValueError("No XHTML/HTML content found in EPUB")

        for cf in content_files:
            try:
                data = zf.read(cf).decode('utf-8', errors='replace')
            except Exception:
                continue

            extractor = EPUBTextExtractor()
            extractor.feed(data)
            chapter_text = extractor.text.strip()

            if chapter_text and len(chapter_text) > 20:
                chapters.append(chapter_text)

    if not chapters:
        raise ValueError("No readable text extracted from EPUB")

    # Try to find title from metadata
    try:
        with zipfile.ZipFile(epub_path, 'r') as zf:
            for f in zf.namelist():
                if f.endswith('.opf'):
                    opf = zf.read(f).decode('utf-8', errors='replace')
                    m = re.search(r'<dc:title[^>]*>([^<]+)</dc:title>', opf)
                    if m:
                        title = m.group(1).strip()
                        break
    except Exception:
        pass

    return title, '\n\n'.join(chapters)


# ── PDF Converter ───────────────────────────────────────────────

def pdf_to_text(pdf_path):
    """Extract text from a PDF file. Requires pdftotext or PyPDF2."""
    title = Path(pdf_path).stem

    # Try pdftotext first (best quality)
    import subprocess
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', '-nopgbrk', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return title, result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fall back to PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        if pages:
            return title, '\n\n'.join(pages)
    except ImportError:
        pass

    raise RuntimeError(
        "Cannot extract PDF text.\n"
        "Install one of:\n"
        "  pip install PyPDF2\n"
        "  apt install poppler-utils  (for pdftotext)"
    )


# ── Text Cleanup ────────────────────────────────────────────────

def clean_text(text, hard_wrap=None):
    """Clean up extracted text for eInk display."""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Collapse runs of blank lines (max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove trailing whitespace per line
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    # Strip leading/trailing whitespace
    text = text.strip()

    # Optionally hard-wrap lines
    if hard_wrap and hard_wrap > 0:
        lines = []
        for para in text.split('\n\n'):
            para = para.replace('\n', ' ')
            if para.startswith('## '):
                lines.append(para)
                lines.append('')
            else:
                words = para.split()
                current = ''
                for w in words:
                    if len(current) + len(w) + 1 <= hard_wrap:
                        current += (' ' + w) if current else w
                    else:
                        lines.append(current)
                        current = w
                if current:
                    lines.append(current)
                lines.append('')  # paragraph break
        text = '\n'.join(lines).strip()

    return text


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Convert EPUB/PDF to plain text for Altoid eInk Reader'
    )
    parser.add_argument('input', help='Input file (.epub or .pdf)')
    parser.add_argument('-o', '--output', help='Output file (default: input.txt)')
    parser.add_argument('-w', '--wrap', type=int, default=0,
                        help='Hard-wrap text at N characters (0 = no wrap, ~21 for eInk display)')
    parser.add_argument('--title', help='Override title (first line of output)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    suffix = input_path.suffix.lower()

    print(f"Converting: {input_path.name} ...")

    if suffix == '.epub':
        title, raw_text = epub_to_text(input_path)
    elif suffix == '.pdf':
        title, raw_text = pdf_to_text(input_path)
    else:
        print(f"Error: unsupported format '{suffix}'. Use .epub or .pdf",
              file=sys.stderr)
        sys.exit(1)

    # Clean text
    text = clean_text(raw_text, hard_wrap=args.wrap)

    # Add title
    final_title = args.title or title
    if not text.startswith('## '):
        text = f"## {final_title}\n\n{text}"

    # Write output
    output_path = Path(args.output) if args.output else input_path.with_suffix('.txt')
    output_path.write_text(text, encoding='utf-8')

    # Stats
    lines = text.count('\n') + 1
    chars = len(text)
    pages_est = max(1, lines // 32)  # ~32 lines per eInk page
    print(f"  → {output_path}")
    print(f"  {chars:,} chars, {lines:,} lines, ~{pages_est} eInk pages")


if __name__ == '__main__':
    main()
