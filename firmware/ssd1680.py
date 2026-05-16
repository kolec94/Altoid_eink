"""
SSD1680 e-Paper Display Driver for MicroPython (Raspberry Pi Pico)
Target: Adafruit 2.9" Tri-Color (Red/Black/White) 128×296

Datasheet: https://cdn-learn.adafruit.com/assets/assets/000/131/641/original/SSD1680.pdf
"""

from machine import Pin, SPI
from time import sleep_ms, ticks_ms, ticks_diff

# ── SSD1680 Command Set ──────────────────────────────────────────
_SW_RESET       = 0x12
_DRIVER_OUTPUT  = 0x01
_DATA_ENTRY     = 0x11
_BORDER_WAVEFORM = 0x3C
_TEMP_SENSOR    = 0x18
_DISPLAY_UPDATE = 0x22
_MASTER_ACTIVATE = 0x20
_WRITE_BW       = 0x24
_WRITE_RED      = 0x26
_SET_RAM_X      = 0x44
_SET_RAM_Y      = 0x45
_SET_RAM_X_COUNT = 0x4E
_SET_RAM_Y_COUNT = 0x4F
_DEEP_SLEEP     = 0x10

class SSD1680:
    """Driver for SSD1680-based tri-color e-Paper displays."""

    def __init__(self, spi, cs, dc, rst, busy,
                 width=128, height=296, rotation=0):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.busy = Pin(busy, Pin.IN)

        self.width = width
        self.height = height
        self.rotation = rotation

        # Buffer size: (width // 8) * height bytes per color plane
        self.row_bytes = (width + 7) // 8
        self.buf_size = self.row_bytes * height

        self._buf_bw = bytearray(self.buf_size)   # Black buffer
        self._buf_red = bytearray(self.buf_size)  # Red buffer

        self._init_display()

    # ── low-level SPI ────────────────────────────────────────────

    def _command(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def _data(self, buf):
        self.cs(0)
        self.dc(1)
        self.spi.write(buf if isinstance(buf, (bytes, bytearray)) else bytearray(buf))
        self.cs(1)

    def _wait_busy(self, timeout_ms=30000):
        start = ticks_ms()
        while self.busy():
            if ticks_diff(ticks_ms(), start) > timeout_ms:
                raise RuntimeError("Display busy timeout")
            sleep_ms(10)

    def _reset(self):
        self.rst(1)
        sleep_ms(10)
        self.rst(0)
        sleep_ms(5)
        self.rst(1)
        sleep_ms(10)
        self._wait_busy()

    # ── initialization ───────────────────────────────────────────

    def _init_display(self):
        self._reset()

        # Software reset
        self._command(_SW_RESET)
        self._wait_busy()

        # Driver output control: 296 lines, gate scanning from G0→G295
        # MUX = height - 1 = 295 = 0x0127
        self._command(_DRIVER_OUTPUT)
        self._data(bytearray([(self.height - 1) & 0xFF,
                              ((self.height - 1) >> 8) & 0xFF,
                              0x00]))

        # Data entry mode: X increment, Y increment
        self._command(_DATA_ENTRY)
        self._data(0x03)

        # Border waveform: follow LUT for VCOM black
        self._command(_BORDER_WAVEFORM)
        self._data(0x03)  # VCOM from register, border=black

        # Temperature sensor: internal
        self._command(_TEMP_SENSOR)
        self._data(0x80)

        # VCOM voltage (critical: panel shows nothing without this!)
        self._command(0x2C)
        self._data(0x36)

        # Gate driving voltage
        self._command(0x03)
        self._data(0x17)

        # Source driving voltage
        self._command(0x04)
        self._data(bytearray([0x41, 0xAE, 0x32]))

        # Display update mode default
        self._command(0x22)
        self._data(0xF4)  # Use clock + LUT, full update
        self._data(0x80)

        # Set RAM X start/end
        self._command(_SET_RAM_X)
        self._data(bytearray([0x00, 0x0F]))  # 0→15 (128 pixels, 16 bytes)

        # Set RAM Y start/end
        self._command(_SET_RAM_Y)
        self._data(bytearray([0x00, 0x00,
                              (self.height - 1) & 0xFF,
                              ((self.height - 1) >> 8) & 0xFF]))

        # Set RAM X address count
        self._command(_SET_RAM_X_COUNT)
        self._data(0x00)

        # Set RAM Y address count
        self._command(_SET_RAM_Y_COUNT)
        self._data(bytearray([0x00, 0x00]))

        # Clear buffers
        self.fill(1)  # white
        self.update()

    # ── drawing ──────────────────────────────────────────────────

    def _set_xy(self, x, y):
        """Set RAM address pointer to (x, y)."""
        self._command(_SET_RAM_X_COUNT)
        self._data(x >> 3)
        self._command(_SET_RAM_Y_COUNT)
        self._data(bytearray([y & 0xFF, (y >> 8) & 0xFF]))

    def _byte_index(self, x, y):
        """Return buffer byte index for pixel (x, y)."""
        return (y * self.row_bytes) + (x >> 3)

    def _bit_mask(self, x):
        """Return bit mask for pixel column within byte."""
        return 0x80 >> (x & 0x07)

    def pixel(self, x, y, bw, red=0):
        """
        Set a single pixel.
        bw: 0=black, 1=white
        red: 0=no red, 1=red
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        idx = self._byte_index(x, y)
        mask = self._bit_mask(x)
        if bw:
            self._buf_bw[idx] |= mask
        else:
            self._buf_bw[idx] &= ~mask
        if red:
            self._buf_red[idx] |= mask
        else:
            self._buf_red[idx] &= ~mask

    def fill(self, color=1):
        """
        Fill entire buffer.
        color: 0=black, 1=white, 2=red
        """
        if color == 0:   # black
            for i in range(self.buf_size):
                self._buf_bw[i] = 0x00
                self._buf_red[i] = 0x00
        elif color == 2:  # red
            for i in range(self.buf_size):
                self._buf_bw[i] = 0xFF
                self._buf_red[i] = 0x00
        else:             # white
            for i in range(self.buf_size):
                self._buf_bw[i] = 0xFF
                self._buf_red[i] = 0xFF

    def fill_rect(self, x, y, w, h, bw, red=0):
        """Fill a rectangle."""
        for dy in range(h):
            for dx in range(w):
                self.pixel(x + dx, y + dy, bw, red)

    def rect(self, x, y, w, h, bw, red=0):
        """Draw a rectangle outline."""
        self.fill_rect(x, y, w, 1, bw, red)
        self.fill_rect(x, y + h - 1, w, 1, bw, red)
        self.fill_rect(x, y, 1, h, bw, red)
        self.fill_rect(x + w - 1, y, 1, h, bw, red)

    # ── update ───────────────────────────────────────────────────

    def update(self):
        """Transfer buffer to display and trigger refresh."""
        self._write_buffers()
        self._refresh()

    def _write_buffers(self):
        """Write BW and RED buffers to display RAM."""
        # Black/White plane
        self._command(_WRITE_BW)
        self._data(self._buf_bw)

        # Red plane
        self._command(_WRITE_RED)
        self._data(self._buf_red)

    def _refresh(self):
        """Trigger display update sequence."""
        # Display update control 2: use clock signal, full update
        self._command(_DISPLAY_UPDATE)
        self._data(0xF4)  # Full update with clock + LUT

        # Master activate
        self._command(_MASTER_ACTIVATE)
        self._wait_busy()

    def sleep(self):
        """Put display into deep sleep mode."""
        self._command(_DEEP_SLEEP)
        self._data(0x01)
