#!/usr/bin/env python3
"""
ebook2txt — Convert EPUB and PDF to plain text for Altoid eInk Reader
=====================================================================

Usage:
    python3 ebook2txt.py book.epub          → book.txt
    python3 ebook2txt.py book.pdf           → book.txt
    python3 ebook2txt.py book.epub -o out.txt
    python3 ebook2txt.py book.pdf -w 60     → wrap at 60 chars
    python3 ebook2txt.py --interactive      → terminal prompts + folder dialog

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
import shlex
import shutil
import subprocess
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


def convert_file(input_path, output_path=None, output_dir=None, hard_wrap=0, title_override=None):
    """Convert an EPUB/PDF file to text. Returns stats for UI/CLI reporting."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} not found")

    suffix = input_path.suffix.lower()

    if suffix == '.epub':
        title, raw_text = epub_to_text(input_path)
    elif suffix == '.pdf':
        title, raw_text = pdf_to_text(input_path)
    else:
        raise ValueError(f"unsupported format '{suffix}'. Use .epub or .pdf")

    text = clean_text(raw_text, hard_wrap=hard_wrap)

    final_title = title_override or title
    if not text.startswith('## '):
        text = f"## {final_title}\n\n{text}"

    if output_path:
        output_path = Path(output_path)
    elif output_dir:
        output_path = Path(output_dir) / input_path.with_suffix('.txt').name
    else:
        output_path = input_path.with_suffix('.txt')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding='utf-8')

    lines = text.count('\n') + 1
    chars = len(text)
    pages_est = max(1, lines // 32)  # ~32 lines per eInk page

    return {
        'input_path': input_path,
        'output_path': output_path,
        'chars': chars,
        'lines': lines,
        'pages_est': pages_est,
    }


def parse_dropped_path(raw_path):
    """Normalize a path pasted or dragged into a terminal."""
    raw_path = raw_path.strip()
    if not raw_path:
        return ''
    try:
        parts = shlex.split(raw_path)
    except ValueError:
        parts = []
    if len(parts) == 1:
        return parts[0]
    return raw_path.strip('\'"')


def choose_output_folder():
    """Open an OS folder dialog when available. Returns a path or an empty string."""
    if sys.platform == 'darwin' and shutil.which('osascript'):
        script = 'POSIX path of (choose folder with prompt "Choose output folder")'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ''

    if shutil.which('zenity'):
        result = subprocess.run(
            ['zenity', '--file-selection', '--directory', '--title=Choose output folder'],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ''

    if shutil.which('kdialog'):
        result = subprocess.run(
            ['kdialog', '--getexistingdirectory', str(Path.home())],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ''

    return ''


def run_interactive():
    """Prompt for input in the terminal and use a folder dialog when possible."""
    print("Altoid eInk Converter")
    print("Drag an EPUB/PDF into this terminal, or paste its path.")
    input_path = parse_dropped_path(input("Input file: "))
    if not input_path:
        raise ValueError("No input file selected")

    print("Opening output folder chooser...")
    output_dir = choose_output_folder()
    if not output_dir:
        print("No folder dialog is available or no folder was selected.")
        print("Drag an output folder into this terminal, or paste its path.")
        output_dir = parse_dropped_path(input("Output folder: "))
    if not output_dir:
        raise ValueError("No output folder selected")

    wrap_raw = input("Wrap width [0, use 21 for screen-width wrapping]: ").strip()
    try:
        wrap = int(wrap_raw or "0")
        if wrap < 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("Wrap width must be a non-negative number") from exc

    title = input("Title override [optional]: ").strip() or None

    result = convert_file(
        input_path,
        output_dir=output_dir,
        hard_wrap=wrap,
        title_override=title,
    )
    print(f"Saved: {result['output_path']}")
    print(f"{result['chars']:,} chars, {result['lines']:,} lines, ~{result['pages_est']} eInk pages")


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Convert EPUB/PDF to plain text for Altoid eInk Reader'
    )
    parser.add_argument('input', nargs='?', help='Input file (.epub or .pdf)')
    parser.add_argument('-o', '--output', help='Output file (default: input.txt)')
    parser.add_argument('-d', '--output-dir', help='Output folder (default: input file folder)')
    parser.add_argument('-w', '--wrap', type=int, default=0,
                        help='Hard-wrap text at N characters (0 = no wrap, ~21 for eInk display)')
    parser.add_argument('--title', help='Override title (first line of output)')
    parser.add_argument('--interactive', action='store_true',
                        help='Prompt for input path and open an output-folder dialog when available')
    args = parser.parse_args()

    if args.interactive:
        try:
            run_interactive()
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    if not args.input:
        parser.error('input is required unless --interactive is used')

    input_path = Path(args.input)
    print(f"Converting: {input_path.name} ...")
    try:
        result = convert_file(
            input_path,
            output_path=args.output,
            output_dir=args.output_dir,
            hard_wrap=args.wrap,
            title_override=args.title,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"  → {result['output_path']}")
    print(f"  {result['chars']:,} chars, {result['lines']:,} lines, ~{result['pages_est']} eInk pages")


if __name__ == '__main__':
    main()
