"""
Display test — verifies wiring of SSD1680 eInk breakout to Pico.
No SD card or buttons required. Upload this as main.py to test.

Expected: draws colored rectangles, text, and border patterns.
Each step takes ~15s (eInk refresh). Whole test ~1 minute.
"""

from machine import Pin, SPI
from time import sleep_ms

# ── Pin assignments (must match your wiring) ───────────────────
PIN_SCK  = 2
PIN_MOSI = 3
PIN_ECS  = 5
PIN_DC   = 6
PIN_RST  = 7
PIN_BUSY = 8
PIN_SRCS = 13  # SRAM CS - hold HIGH to disable

WIDTH  = 128
HEIGHT = 296

# ── Low-level SSD1680 driver (minimal, no imports needed) ─────

class SSD1680:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.busy = Pin(busy, Pin.IN)
        self.row_bytes = (WIDTH + 7) // 8  # 16
        self.buf_size = self.row_bytes * HEIGHT
        self.bw = bytearray(self.buf_size)
        self.red = bytearray(self.buf_size)
        self._init()

    def _cmd(self, cmd):
        self.cs(0); self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def _data(self, buf):
        self.cs(0); self.dc(1)
        self.spi.write(buf if isinstance(buf, (bytes, bytearray)) else bytearray(buf))
        self.cs(1)

    def _wait(self):
        t = 0
        while self.busy():
            sleep_ms(10); t += 10
            if t > 30000:
                raise RuntimeError("BUSY timeout — check BUSY pin wiring")

    def _init(self):
        self.rst(1); sleep_ms(10)
        self.rst(0); sleep_ms(5)
        self.rst(1); sleep_ms(10)
        self._wait()

        self._cmd(0x12); self._wait()                    # SW reset
        self._cmd(0x01); self._data([0x27, 0x01, 0x00])  # 296 lines
        self._cmd(0x11); self._data(0x03)                 # data entry
        self._cmd(0x3C); self._data(0x03)                 # border VCOM
        self._cmd(0x18); self._data(0x80)                 # temp sensor
        self._cmd(0x2C); self._data(0x36)                 # VCOM voltage
        self._cmd(0x03); self._data(0x17)                 # gate voltage
        self._cmd(0x04); self._data([0x41, 0xAE, 0x32])  # source voltage
        self._cmd(0x44); self._data([0x00, 0x0F])         # RAM X range
        self._cmd(0x45); self._data([0x00, 0x00, 0x27, 0x01])  # RAM Y range
        self._cmd(0x4E); self._data(0x00)
        self._cmd(0x4F); self._data([0x00, 0x00])

        self.clear()
        self.update()

    def clear(self):
        for i in range(self.buf_size):
            self.bw[i] = 0xFF
            self.red[i] = 0xFF

    def pixel(self, x, y, bw, red=0):
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return
        idx = (y * self.row_bytes) + (x >> 3)
        mask = 0x80 >> (x & 7)
        if bw:
            self.bw[idx] |= mask
        else:
            self.bw[idx] &= ~mask
        if red:
            self.red[idx] |= mask
        else:
            self.red[idx] &= ~mask

    def fill_rect(self, x, y, w, h, bw, red=0):
        for dy in range(h):
            for dx in range(w):
                self.pixel(x + dx, y + dy, bw, red)

    def rect(self, x, y, w, h, bw, red=0):
        self.fill_rect(x, y, w, 1, bw, red)
        self.fill_rect(x, y + h - 1, w, 1, bw, red)
        self.fill_rect(x, y, 1, h, bw, red)
        self.fill_rect(x + w - 1, y, 1, h, bw, red)

    def char(self, x, y, ch, bw=0, red=0):
        """Simple 5x7 font hardcoded for A-Z, 0-9, space."""
        FONT = {
            'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x46, 0x49, 0x49, 0x49, 0x31],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x42, 0x61, 0x51, 0x49, 0x46],
            '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
            '7': [0x01, 0x71, 0x09, 0x05, 0x03],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            '.': [0x00, 0x60, 0x60, 0x00, 0x00],
            '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
            ':': [0x00, 0x36, 0x36, 0x00, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x08],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
        }
        glyph = FONT.get(ch, FONT[' '])
        for col in range(5):
            bits = glyph[col]
            for row in range(7):
                if bits & (1 << row):
                    self.pixel(x + col, y + row, bw, red)

    def text(self, x, y, s, bw=0, red=0):
        cx = x
        for ch in s:
            if cx + 6 > WIDTH:
                cx = x; y += 9
            self.char(cx, y, ch, bw, red)
            cx += 6

    def update(self):
        self._cmd(0x24); self._data(self.bw)
        self._cmd(0x26); self._data(self.red)
        self._cmd(0x22); self._data(0xF4)
        self._cmd(0x20)
        self._wait()


# ── Test sequence ──────────────────────────────────────────────

def test():
    print("Initializing SPI...")
    spi = SPI(0, baudrate=4_000_000, polarity=0, phase=0, bits=8,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI))

    # Hold SRAM chip select HIGH to disable SRAM
    srcs = Pin(PIN_SRCS, Pin.OUT, value=1)
    print("SRCS held HIGH")

    print("Initializing display...")
    d = SSD1680(spi, cs=PIN_ECS, dc=PIN_DC, rst=PIN_RST, busy=PIN_BUSY)
    print("Display OK!")

    # ── Test 1: Red/Black/White rectangles ─────────────────────
    print("\n[Test 1/5] Color bars...")
    d.clear()
    d.fill_rect(0,   0, WIDTH, 50, bw=0, red=0)   # black bar
    d.fill_rect(0,  50, WIDTH, 50, bw=1, red=0)   # red bar
    d.fill_rect(0, 100, WIDTH, 50, bw=0, red=1)   # mixed (black + red = ?)
    d.text(4, 114, "BLACK BAR", bw=1, red=0)
    d.text(4, 150, "RED BAR", bw=1, red=0)
    d.text(4, 200, "WHITE AREA", bw=0, red=0)
    d.update()
    print("  > Should see: black, red, and white horizontal bars")

    # ── Test 2: Checkerboard ───────────────────────────────────
    print("\n[Test 2/5] Checkerboard pattern...")
    d.clear()
    size = 16
    for row in range(HEIGHT // size):
        for col in range(WIDTH // size):
            c = (row + col) % 2
            d.fill_rect(col * size, row * size, size, size, bw=c, red=0)
    d.update()
    print("  > Should see: black and white checkerboard")

    # ── Test 3: Border + text ──────────────────────────────────
    print("\n[Test 3/5] Border + label...")
    d.clear()
    d.rect(0, 0, WIDTH, HEIGHT, bw=0, red=0)
    d.rect(3, 3, WIDTH-6, HEIGHT-6, bw=0, red=1)
    d.text(8, 130, "WIRING OK!", bw=0, red=0)
    d.text(8, 142, "SCK MOSI DC RST", bw=0, red=0)
    d.text(8, 154, "ECS BUSY VIN GND", bw=0, red=0)
    d.update()
    print("  > Should see: double border (black outer, red inner) + text")

    # ── Test 4: All characters ─────────────────────────────────
    print("\n[Test 4/5] Character set...")
    d.clear()
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    d.text(2, 2, chars, bw=0, red=0)
    chars = "0123456789.-/!ABCDEF"
    d.text(2, 14, chars, bw=0, red=1)  # red text
    d.text(2, 28, "ALTOID EINK READER", bw=0, red=0)
    d.text(2, 42, "TEST V0.1", bw=0, red=0)
    d.text(2, 60, "ALL PINS CONNECTED:", bw=0, red=0)
    d.text(2, 72, "GP2:SCK GP3:MOSI", bw=0, red=0)
    d.text(2, 84, "GP5:ECS GP6:D/C", bw=0, red=0)
    d.text(2, 96, "GP7:RST GP8:BUSY", bw=0, red=0)
    d.rect(0, 0, WIDTH, HEIGHT, bw=0, red=0)
    d.update()
    print("  > Should see: alphabet, numbers, pin labels")

    # ── Test 5: Horizontal/vertical lines ──────────────────────
    print("\n[Test 5/5] Grid lines...")
    d.clear()
    for y in range(0, HEIGHT, 20):
        d.fill_rect(0, y, WIDTH, 1, bw=0, red=0)
    for x in range(0, WIDTH, 20):
        d.fill_rect(x, 0, 1, HEIGHT, bw=0, red=0)
    d.text(10, 270, "GRID TEST PASSED", bw=0, red=1)
    d.update()
    print("  > Should see: fine grid with red footer text")

    print("\n=== All 5 tests complete! ===")
    print("If all patterns displayed correctly, your wiring is good.")
    print("Ready to deploy the full reader firmware.")


test()
