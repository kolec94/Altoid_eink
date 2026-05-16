"""
Altoid eInk Reader — Main Application
Reads .txt files from SD card on Adafruit 2.9" Tri-Color eInk (SSD1680).
Navigation via 3 buttons: UP, DOWN, SELECT.
"""

from machine import Pin, SPI
from time import sleep_ms, ticks_ms, ticks_diff
import os

from ssd1680 import SSD1680
from sdcard import SDCard, mount_sd
from font5x7 import FONT_WIDTH, FONT_HEIGHT, FONT_SPACING, draw_text, draw_text_wrap

# ── Pin Assignments ─────────────────────────────────────────────
PIN_SCK  = 2
PIN_MOSI = 3
PIN_MISO = 4
PIN_ECS  = 5   # E-Ink CS
PIN_DC   = 6
PIN_RST  = 7
PIN_BUSY = 8
PIN_SDCS = 9   # SD Card CS

PIN_BTN_UP   = 10
PIN_BTN_DOWN = 11
PIN_BTN_SEL  = 12
PIN_SRCS     = 13  # SRAM chip select
PIN_ENA      = 14  # Display power enable

# ── Display specs ───────────────────────────────────────────────
WIDTH  = 128
HEIGHT = 296

# Layout
MARGIN = 2
HEADER_H = 12
FOOTER_H = 10
BODY_Y = MARGIN + HEADER_H + 2
BODY_H = HEIGHT - BODY_Y - FOOTER_H - MARGIN
TEXT_W = WIDTH - 2 * MARGIN
MAX_LINES = BODY_H // (FONT_HEIGHT + FONT_SPACING)
CHARS_PER_LINE = TEXT_W // (FONT_WIDTH + FONT_SPACING)


class EInkReader:
    def __init__(self):
        # ── SPI bus (shared between display and SD) ─────────────
        self.spi = SPI(0,
                       baudrate=4_000_000,
                       polarity=0,
                       phase=0,
                       bits=8,
                       sck=Pin(PIN_SCK),
                       mosi=Pin(PIN_MOSI),
                       miso=Pin(PIN_MISO))

        # ── Display ─────────────────────────────────────────────
        self.display = SSD1680(self.spi,
                               cs=PIN_ECS,
                               dc=PIN_DC,
                               rst=PIN_RST,
                               busy=PIN_BUSY,
                               width=WIDTH,
                               height=HEIGHT)

        # ── SD Card ─────────────────────────────────────────────
        self.sd = None
        self.sd_mounted = False

        # ── Buttons (internal pull-up, active low) ──────────────
        self.btn_up   = Pin(PIN_BTN_UP,   Pin.IN, Pin.PULL_UP)
        self.btn_down = Pin(PIN_BTN_DOWN, Pin.IN, Pin.PULL_UP)
        self.btn_sel  = Pin(PIN_BTN_SEL,  Pin.IN, Pin.PULL_UP)

        # ── SRAM chip select (hold HIGH to disable) ────────────
        self.srcs = Pin(PIN_SRCS, Pin.OUT, value=1)

        # ── Display power enable (must be HIGH) ──────────────
        self.ena = Pin(PIN_ENA, Pin.OUT, value=1)

        # ── State ───────────────────────────────────────────────
        self.files = []
        self.current_file = ''
        self.file_content = ''
        self.pages = []
        self.current_page = 0
        self.mode = 'menu'  # 'menu' | 'reading'
        self.menu_sel = 0

        # Debounce state
        self._btn_state = {PIN_BTN_UP: 1, PIN_BTN_DOWN: 1, PIN_BTN_SEL: 1}
        self._btn_time  = {PIN_BTN_UP: 0, PIN_BTN_DOWN: 0, PIN_BTN_SEL: 0}
        self.DEBOUNCE_MS = 50

    # ── Button handling ─────────────────────────────────────────

    def _btn_pressed(self, pin):
        """Return True on falling edge (debounced)."""
        now = ticks_ms()
        val = pin.value()
        pn = int(str(pin).split('(')[1].split(',')[0])
        if val == 0 and self._btn_state[pn] == 1:
            if ticks_diff(now, self._btn_time[pn]) > self.DEBOUNCE_MS:
                self._btn_state[pn] = 0
                self._btn_time[pn] = now
                return True
        elif val == 1:
            self._btn_state[pn] = 1
        return False

    def _wait_button(self, timeout_ms=0):
        """Wait for any button press. Returns (pin_name, hold_ms) or None."""
        start = ticks_ms()
        pressed = None
        hold_start = 0

        while True:
            if timeout_ms and ticks_diff(ticks_ms(), start) > timeout_ms:
                return None

            for btn_pin, name in [(self.btn_up, 'up'),
                                   (self.btn_down, 'down'),
                                   (self.btn_sel, 'sel')]:
                if self._btn_pressed(btn_pin):
                    pressed = (name, 0)
                    hold_start = ticks_ms()
                    break

            if pressed:
                # Wait for release, measure hold time
                pin = {'up': self.btn_up, 'down': self.btn_down,
                       'sel': self.btn_sel}[pressed[0]]
                while pin.value() == 0:
                    sleep_ms(10)
                    if ticks_diff(ticks_ms(), hold_start) > 2000:
                        break
                hold_dur = ticks_diff(ticks_ms(), hold_start)
                return (pressed[0], hold_dur)

            sleep_ms(10)

    # ── SD Card ─────────────────────────────────────────────────

    def init_sd(self):
        """Initialize and mount SD card."""
        try:
            self.sd, sectors = mount_sd(self.spi, PIN_SDCS)
            self.sd_mounted = True
            print(f"SD OK: {sectors} sectors, {self.sd.capacity_mb} MB")
            return True
        except Exception as e:
            print(f"SD error: {e}")
            self.sd_mounted = False
            return False

    def scan_files(self):
        """List .txt files in /sd root."""
        if not self.sd_mounted:
            return []
        try:
            files = []
            for f in os.listdir('/sd'):
                if f.lower().endswith('.txt'):
                    files.append(f)
            files.sort()
            return files
        except Exception as e:
            print(f"List error: {e}")
            return []

    def load_file(self, filename):
        """Load text content from file."""
        try:
            path = f'/sd/{filename}'
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Read error: {e}")
            return None

    # ── Pagination ──────────────────────────────────────────────

    def paginate(self, text):
        """Split text into display pages with word wrap."""
        pages = []
        lines = []
        current_line = ''

        for ch in text:
            if ch == '\n':
                lines.append(current_line)
                current_line = ''
            elif ch == ' ':
                if len(current_line) + 1 > CHARS_PER_LINE:
                    lines.append(current_line)
                    current_line = ''
                else:
                    current_line += ch
            else:
                if len(current_line) >= CHARS_PER_LINE:
                    lines.append(current_line)
                    current_line = ch
                else:
                    current_line += ch

        if current_line:
            lines.append(current_line)

        # Split lines into pages
        for i in range(0, len(lines), MAX_LINES):
            pages.append(lines[i:i + MAX_LINES])

        return pages

    # ── Display rendering ───────────────────────────────────────

    def _draw_header(self, title, red=False):
        """Draw header bar with title."""
        bw = 0
        r = 1 if red else 0
        draw_text(self.display, MARGIN, MARGIN, title[:21], bw=bw, red=r)
        # Underline
        self.display.fill_rect(MARGIN, MARGIN + HEADER_H - 2,
                                WIDTH - 2 * MARGIN, 1, bw=bw, red=r)

    def _draw_footer(self, text):
        """Draw footer bar."""
        y = HEIGHT - FOOTER_H - MARGIN
        self.display.fill_rect(0, y - 1, WIDTH, 1, bw=0, red=0)
        draw_text(self.display, MARGIN, y + 1, text[:21], bw=0, red=0)

    def show_menu(self):
        """Render file selection menu."""
        self.display.fill(1)  # white

        self._draw_header('Altoid eInk Reader', red=True)

        files = self.files
        y = BODY_Y
        start = max(0, self.menu_sel - (MAX_LINES - 1))
        end = min(len(files), start + MAX_LINES)

        for i in range(start, end):
            marker = '>' if i == self.menu_sel else ' '
            line = f"{marker}{files[i]}"
            bw = 0 if i == self.menu_sel else 0
            red = 1 if i == self.menu_sel else 0
            draw_text(self.display, MARGIN + 2, y, line[:CHARS_PER_LINE - 2],
                      bw=bw, red=red)
            y += FONT_HEIGHT + FONT_SPACING

        if not files:
            draw_text(self.display, MARGIN + 2, BODY_Y,
                      'No .txt files found', bw=0, red=1)
            draw_text(self.display, MARGIN + 2, BODY_Y + 10,
                      'Insert SD card + reset', bw=0, red=0)

        page_info = f"{self.menu_sel + 1}/{len(files)}" if files else "0/0"
        self._draw_footer(f"[UP/DOWN]sel  [SEL]open  {page_info}")

        self.display.update()

    def show_page(self, page_num):
        """Render a single page of the current file."""
        self.display.fill(1)  # white

        # Header with filename (red)
        fname = self.current_file
        if len(fname) > 19:
            fname = fname[:18] + '~'
        self._draw_header(fname, red=True)

        # Body text
        y = BODY_Y
        if self.pages and page_num < len(self.pages):
            for line in self.pages[page_num]:
                draw_text(self.display, MARGIN, y, line[:CHARS_PER_LINE], bw=0, red=0)
                y += FONT_HEIGHT + FONT_SPACING

        # Footer
        total = len(self.pages)
        self._draw_footer(f'[UP/DOWN]nav  [SEL]menu  {page_num + 1}/{total}')

        self.display.update()

    def show_error(self, msg):
        """Display error message."""
        self.display.fill(1)
        self._draw_header('Error', red=True)
        draw_text(self.display, MARGIN, BODY_Y, msg, bw=0, red=1)
        self._draw_footer('[SEL]continue')
        self.display.update()

    # ── Main loop ───────────────────────────────────────────────

    def run(self):
        """Main application loop."""
        # Startup screen
        self.display.fill(1)
        draw_text(self.display, MARGIN, 40, 'Altoid eInk', bw=0, red=1)
        draw_text(self.display, MARGIN, 50, 'Reader v0.1', bw=0, red=0)
        draw_text(self.display, MARGIN, 65, 'Loading...', bw=0, red=0)
        self.display.update()

        # Init SD card
        if not self.init_sd():
            self.show_error('SD card not found.\nPlease insert card\nand reset device.')
            while True:
                sleep_ms(100)
            return

        # Scan files
        self.files = self.scan_files()
        self.mode = 'menu'
        self.menu_sel = 0
        self.show_menu()

        # Event loop
        while True:
            btn = self._wait_button(timeout_ms=200)

            if self.mode == 'menu':
                if btn:
                    name, hold = btn
                    if name == 'up':
                        if self.files:
                            self.menu_sel = (self.menu_sel - 1) % len(self.files)
                        self.show_menu()
                    elif name == 'down':
                        if self.files:
                            self.menu_sel = (self.menu_sel + 1) % len(self.files)
                        self.show_menu()
                    elif name == 'sel':
                        if self.files:
                            self._open_file(self.files[self.menu_sel])
                        else:
                            # Rescan
                            self.files = self.scan_files()
                            self.show_menu()

            elif self.mode == 'reading':
                if btn:
                    name, hold = btn
                    if name == 'up':
                        if self.current_page > 0:
                            self.current_page -= 1
                        self.show_page(self.current_page)
                    elif name == 'down':
                        if self.current_page < len(self.pages) - 1:
                            self.current_page += 1
                        self.show_page(self.current_page)
                    elif name == 'sel':
                        # Back to menu
                        self.mode = 'menu'
                        self.show_menu()

            sleep_ms(10)

    def _open_file(self, filename):
        """Open a file and enter reading mode."""
        content = self.load_file(filename)
        if content is None:
            self.show_error(f'Failed to read:\n{filename}')
            self._wait_button(timeout_ms=5000)
            self.show_menu()
            return

        self.current_file = filename
        self.file_content = content
        self.pages = self.paginate(content)
        self.current_page = 0
        self.mode = 'reading'
        self.show_page(0)


# ── Entry point ─────────────────────────────────────────────────
def main():
    reader = EInkReader()
    reader.run()


if __name__ == '__main__':
    main()
