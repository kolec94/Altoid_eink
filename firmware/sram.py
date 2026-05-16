"""
Minimal 23LC1024 / 23K256 SPI SRAM driver for MicroPython.
Used with the ThinkInk/EYESPI onboard memory chip via MEMCS.
"""

from machine import Pin

SRAM_READ  = 0x03
SRAM_WRITE = 0x02
SRAM_RDSR  = 0x05
SRAM_WRSR  = 0x01


class SRAM:
    """Microchip 23LC1024 (128KB) SPI SRAM."""

    def __init__(self, spi, cs_pin, baudrate=8_000_000):
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT, value=1)

        # Enable sequential mode
        self.cs(0)
        spi.write(bytearray([SRAM_WRSR, 0x43]))
        self.cs(1)

    def write(self, addr, data):
        """Write data buffer starting at address."""
        self.cs(0)
        self.spi.write(bytearray([
            SRAM_WRITE,
            (addr >> 8) & 0xFF,
            addr & 0xFF
        ]))
        self.spi.write(data if isinstance(data, (bytes, bytearray)) else bytearray(data))
        self.cs(1)

    def start_read(self, addr=0):
        """Begin a sequential read at address. Returns nothing — 
        subsequent SPI reads will stream data from SRAM.
        Keeps CS low for streaming."""
        self.cs(0)
        self.spi.write(bytearray([
            SRAM_READ,
            (addr >> 8) & 0xFF,
            addr & 0xFF
        ]))
        # CS stays low — caller must call cs(1) after reading

    def read_byte(self):
        """Read one byte from an active sequential read."""
        return self.spi.read(1)[0]

    def end_read(self):
        """End a sequential read."""
        self.cs(1)


def transfer_byte(spi, data):
    """Send one byte on MOSI, return the byte received on MISO."""
    spi.write(bytearray([data]))
    return spi.read(1)[0]
