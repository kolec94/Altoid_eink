"""
Micro SD Card Reader via SPI — MicroPython Block Device
========================================================
For Adafruit eInk breakout's built-in microSD slot (SSD1680 board).
Implements MicroPython's block device protocol for os.mount().

References:
  - MicroPython sdcard.py (SPI mode)
  - SD Card Physical Layer Simplified Specification v8.00
"""

from machine import Pin
from time import sleep_ms
import os


class SDCard:
    """SPI SD Card block device for MicroPython."""

    # ── Commands ─────────────────────────────────────────────────
    CMD0  = 0x40      # GO_IDLE_STATE
    CMD1  = 0x41      # SEND_OP_COND (MMC)
    CMD8  = 0x48      # SEND_IF_COND
    CMD9  = 0x49      # SEND_CSD
    CMD10 = 0x4A      # SEND_CID
    CMD12 = 0x4C      # STOP_TRANSMISSION
    CMD13 = 0x4D      # SEND_STATUS
    CMD16 = 0x50      # SET_BLOCKLEN
    CMD17 = 0x51      # READ_SINGLE_BLOCK
    CMD18 = 0x52      # READ_MULTIPLE_BLOCK
    CMD24 = 0x58      # WRITE_BLOCK
    CMD25 = 0x59      # WRITE_MULTIPLE_BLOCK
    CMD55 = 0x40 + 55 # APP_CMD
    CMD58 = 0x40 + 58 # READ_OCR
    ACMD41= 0x80 | (0x40 + 41)  # SD_SEND_OP_COND

    # ── Response tokens ──────────────────────────────────────────
    R1_IDLE_STATE      = 0x01
    R1_ILLEGAL_COMMAND = 0x04
    R1_READY           = 0x00
    DATA_START_BLOCK   = 0xFE
    DATA_START_WRITE   = 0xFC
    DATA_STOP_TRAN     = 0xFD

    def __init__(self, spi, cs_pin, baudrate=5_000_000):
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.baudrate = baudrate
        self._sectors = 0
        self._is_sdhc = False   # SDHC/SDXC vs SDSC
        self._initialized = False

    # ── Low-level SPI ────────────────────────────────────────────

    def _cmd(self, cmd, arg=0, crc=0x95):
        """Send command, return R1 response byte."""
        self.cs(0)
        self.spi.write(bytearray([
            cmd,
            (arg >> 24) & 0xFF,
            (arg >> 16) & 0xFF,
            (arg >> 8) & 0xFF,
            arg & 0xFF,
            crc
        ]))
        # Read up to 8 bytes looking for non-0xFF (R1 response)
        for _ in range(8):
            r = self.spi.read(1)[0]
            if r != 0xFF:
                break
        self.cs(1)
        return r

    def _read_data_token(self):
        """Wait for and return the data start token."""
        for _ in range(5000):
            t = self.spi.read(1)[0]
            if t == self.DATA_START_BLOCK:
                return t
            if t != 0xFF:
                return t
        return 0xFF

    # ── Block device protocol ────────────────────────────────────

    def readblocks(self, block_num, buf, offset=0):
        """
        Read one or more blocks into buf starting at offset.
        Number of blocks = len(buf) // 512.
        Required by MicroPython block device protocol.
        """
        nblocks = len(buf) // 512
        if nblocks == 0:
            return 0

        # If SDSC, use byte addressing
        addr = block_num if self._is_sdhc else block_num * 512

        if nblocks == 1:
            # Single block read
            if self._cmd(self.CMD17, addr, 0xFF) != 0:
                return -1
            self.cs(0)
            if self._read_data_token() != self.DATA_START_BLOCK:
                self.cs(1)
                return -1
            self.spi.readinto(buf[offset:offset + 512])
            self.spi.read(2)  # CRC
            self.cs(1)
        else:
            # Multi-block read
            if self._cmd(self.CMD18, addr, 0xFF) != 0:
                return -1
            self.cs(0)
            for i in range(nblocks):
                if self._read_data_token() != self.DATA_START_BLOCK:
                    self.cs(1)
                    return -1
                start = offset + i * 512
                self.spi.readinto(buf[start:start + 512])
                self.spi.read(2)  # CRC
            # Stop transmission
            self.spi.write(bytearray([self.CMD12, 0, 0, 0, 0, 0x95]))
            self.spi.read(1)
            self.cs(1)

        return 0

    def writeblocks(self, block_num, buf, offset=0):
        """
        Write one or more blocks from buf starting at offset.
        Number of blocks = len(buf) // 512.
        Required by MicroPython block device protocol.
        """
        nblocks = len(buf) // 512
        if nblocks == 0:
            return 0

        addr = block_num if self._is_sdhc else block_num * 512

        if nblocks == 1:
            if self._cmd(self.CMD24, addr, 0xFF) != 0:
                return -1
            self.cs(0)
            self.spi.write(b'\xFE')  # Start block token
            self.spi.write(buf[offset:offset + 512])
            self.spi.write(b'\xFF\xFF')  # dummy CRC
            # Wait for write to complete
            for _ in range(1000):
                if self.spi.read(1)[0] != 0:
                    break
            self.cs(1)
            # Wait while card is busy
            self.spi.read(1)
        else:
            # Pre-erase for multi-block write
            self._cmd(self.CMD55, 0, 0xFF)  # ACMD prefix
            if self._cmd(self.ACMD41, 0, 0xFF) != 0:
                return -1
            if self._cmd(self.CMD25, addr, 0xFF) != 0:
                return -1
            self.cs(0)
            for i in range(nblocks):
                self.spi.write(b'\xFC')  # Start multi-block token
                start = offset + i * 512
                self.spi.write(buf[start:start + 512])
                self.spi.write(b'\xFF\xFF')  # dummy CRC
                for _ in range(1000):
                    if self.spi.read(1)[0] != 0:
                        break
            self.spi.write(b'\xFD')  # Stop transaction
            self.cs(1)
            self.spi.read(1)  # Wait busy

        return 0

    def ioctl(self, op, arg):
        """
        Block device control.
        op=1: init
        op=4: get number of blocks
        op=5: get block size
        op=6: sync
        """
        if op == 1:  # INIT
            return 0
        elif op == 4:  # BLOCK_COUNT
            return self._sectors
        elif op == 5:  # BLOCK_SIZE
            return 512
        elif op == 6:  # SYNC
            return 0
        return -1

    # ── Initialization ───────────────────────────────────────────

    def init_card(self):
        """Initialize SD card. Returns number of sectors (512-byte blocks)."""
        # Slow SPI for init
        self.spi.init(baudrate=400_000)

        # 80+ clock cycles with CS high (dummy clocks)
        self.cs(1)
        for _ in range(10):
            self.spi.write(b'\xFF')

        # CMD0: go to idle state
        for _ in range(10):
            if self._cmd(self.CMD0, 0, 0x95) == self.R1_IDLE_STATE:
                break
        else:
            raise OSError("SD: no response to CMD0")

        # CMD8: check interface condition (SDv2+)
        r = self._cmd(self.CMD8, 0x1AA, 0x87)
        if r == self.R1_IDLE_STATE:
            # Read R7 response (4 bytes)
            self.cs(0)
            r7 = self.spi.read(4)
            self.cs(1)
            if r7[2] != 0x01 or r7[3] != 0xAA:
                raise OSError("SD: voltage range not supported")
            is_sdv2 = True
        elif r & self.R1_ILLEGAL_COMMAND:
            is_sdv2 = False  # SDv1 or MMC
        else:
            raise OSError(f"SD: CMD8 error 0x{r:02X}")

        # ACMD41: initialize card
        for attempt in range(500):
            self._cmd(self.CMD55, 0, 0xFF)      # APP_CMD prefix
            r = self._cmd(self.ACMD41, 0x40000000 if is_sdv2 else 0, 0xFF)
            if r == self.R1_READY:
                break
            sleep_ms(10)
        else:
            raise OSError("SD: ACMD41 timeout — card not ready")

        # CMD58: read OCR (check SDHC/SDXC)
        r = self._cmd(self.CMD58, 0, 0xFF)
        if r != 0:
            raise OSError(f"SD: CMD58 error 0x{r:02X}")
        self.cs(0)
        ocr = self.spi.read(4)
        self.cs(1)
        self._is_sdhc = (ocr[0] & 0x40) != 0  # CCS bit

        # CMD16: set block length to 512 (for SDSC only)
        if not self._is_sdhc:
            r = self._cmd(self.CMD16, 512, 0xFF)
            if r != 0:
                raise OSError(f"SD: SET_BLOCKLEN error 0x{r:02X}")

        # CMD9: read CSD to determine capacity
        r = self._cmd(self.CMD9, 0, 0xFF)
        if r != 0:
            raise OSError(f"SD: SEND_CSD error 0x{r:02X}")
        self.cs(0)
        if self._read_data_token() != self.DATA_START_BLOCK:
            self.cs(1)
            raise OSError("SD: CSD read failed")
        csd = bytearray(16)
        self.spi.readinto(csd)
        self.spi.read(2)  # CRC
        self.cs(1)

        # Parse CSD
        csd_version = (csd[0] >> 6) & 0x03
        if csd_version == 0:  # CSD v1.0 (SDSC)
            c_size = ((csd[6] & 0x03) << 10) | (csd[7] << 2) | ((csd[8] >> 6) & 0x03)
            c_size_mult = ((csd[9] & 0x03) << 1) | ((csd[10] >> 7) & 0x01)
            read_bl_len = csd[5] & 0x0F
            self._sectors = (c_size + 1) * (1 << (c_size_mult + 2)) * (1 << (read_bl_len - 9))
        elif csd_version == 1:  # CSD v2.0 (SDHC/SDXC)
            c_size = ((csd[7] & 0x3F) << 16) | (csd[8] << 8) | csd[9]
            self._sectors = (c_size + 1) * 1024
        else:
            raise OSError(f"SD: unknown CSD version {csd_version}")

        # Full speed SPI
        self.spi.init(baudrate=self.baudrate)
        self._initialized = True
        return self._sectors

    # ── Properties ───────────────────────────────────────────────

    @property
    def sectors(self):
        return self._sectors

    @property
    def capacity_mb(self):
        return (self._sectors * 512) // (1024 * 1024)


# ── Convenience ──────────────────────────────────────────────────

def mount_sd(spi, cs_pin, path='/sd'):
    """Initialize SD card and mount filesystem at path."""
    sd = SDCard(spi, cs_pin)
    sectors = sd.init_card()
    try:
        os.mount(sd, path)
    except OSError:
        pass  # Already mounted
    return sd, sectors
