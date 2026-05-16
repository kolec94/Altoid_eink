"""
Display test for Adafruit 2.9" Tri-Color eInk Breakout (PID 1028)
SSD1680 with internal RAM — direct SPI writes, no external SRAM.
"""

from machine import Pin, SPI
from time import sleep_ms

PIN_SCK  = 2
PIN_MOSI = 3
PIN_ECS  = 5
PIN_DC   = 6
PIN_RST  = 7
PIN_BUSY = 8

W, H = 128, 296
BE = 16  # bytes/row
BS = BE * H  # buffer size

spi = SPI(0, baudrate=4_000_000, sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI))
cs = Pin(PIN_ECS, Pin.OUT, value=1)
dc = Pin(PIN_DC, Pin.OUT, value=0)
rst = Pin(PIN_RST, Pin.OUT, value=1)
busy = Pin(PIN_BUSY, Pin.IN)

def cmd(c):
    cs(0); dc(0); spi.write(bytes([c])); cs(1)

def data(b):
    cs(0); dc(1); spi.write(b); cs(1)

def wait():
    t = 0
    while busy():
        sleep_ms(10); t += 10
        if t > 30000: raise Exception("BUSY timeout")

# ── Init (Adafruit-compatible sequence) ────────────────────────
print("Hardware reset...")
rst(1); sleep_ms(100)
rst(0); sleep_ms(100)
rst(1); sleep_ms(100)
wait()
print("  OK")

print("Soft reset...")
cmd(0x12)
wait()
print("  OK")

print("Driver output control (296 lines)...")
cmd(0x01); data(b'\x27\x01\x00')

print("Data entry mode...")
cmd(0x11); data(b'\x03')

print("VCOM voltage...")
cmd(0x2C); data(b'\x36')

print("Gate voltage...")
cmd(0x03); data(b'\x17')

print("Source voltage (VSH1=15V, VSH2=5V, VSL=-15V)...")
cmd(0x04); data(b'\x41\x00\x32')  # ← 0x00 not 0xAE!

print("RAM X range...")
cmd(0x44); data(b'\x00\x0F')

print("RAM Y range...")
cmd(0x45); data(b'\x00\x00\x27\x01')

print("Border waveform...")
cmd(0x3C); data(b'\x05')

print("Temperature sensor...")
cmd(0x18); data(b'\x80')

print("RAM X count...")
cmd(0x4E); data(b'\x00')

print("RAM Y count...")
cmd(0x4F); data(b'\x00\x00')

wait()
print("Init complete!")

# ── Buffer helpers ─────────────────────────────────────────────
def pixel(bw, rd, x, y, b, r):
    if not (0 <= x < W and 0 <= y < H): return
    idx = (y * BE) + (x >> 3)
    m = 0x80 >> (x & 7)
    if b: bw[idx] |= m
    else: bw[idx] &= ~m
    if r: rd[idx] |= m
    else: rd[idx] &= ~m

def fill_rect(bw, rd, x, y, w, h, b, r):
    for dy in range(h):
        for dx in range(w):
            pixel(bw, rd, x+dx, y+dy, b, r)

def rect(bw, rd, x, y, w, h, b, r):
    fill_rect(bw, rd, x, y, w, 1, b, r)
    fill_rect(bw, rd, x, y+h-1, w, 1, b, r)
    fill_rect(bw, rd, x, y, 1, h, b, r)
    fill_rect(bw, rd, x+w-1, y, 1, h, b, r)

def char(bw, rd, x, y, ch, b=0, r=0):
    F = {
        'A':[0x7E,0x11,0x11,0x11,0x7E],'B':[0x7F,0x49,0x49,0x49,0x36],
        'C':[0x3E,0x41,0x41,0x41,0x22],'D':[0x7F,0x41,0x41,0x22,0x1C],
        'E':[0x7F,0x49,0x49,0x49,0x41],'F':[0x7F,0x09,0x09,0x09,0x01],
        'G':[0x3E,0x41,0x49,0x49,0x7A],'H':[0x7F,0x08,0x08,0x08,0x7F],
        'I':[0x00,0x41,0x7F,0x41,0x00],'J':[0x20,0x40,0x41,0x3F,0x01],
        'K':[0x7F,0x08,0x14,0x22,0x41],'L':[0x7F,0x40,0x40,0x40,0x40],
        'M':[0x7F,0x02,0x0C,0x02,0x7F],'N':[0x7F,0x04,0x08,0x10,0x7F],
        'O':[0x3E,0x41,0x41,0x41,0x3E],'P':[0x7F,0x09,0x09,0x09,0x06],
        'Q':[0x3E,0x41,0x51,0x21,0x5E],'R':[0x7F,0x09,0x19,0x29,0x46],
        'S':[0x46,0x49,0x49,0x49,0x31],'T':[0x01,0x01,0x7F,0x01,0x01],
        'U':[0x3F,0x40,0x40,0x40,0x3F],'V':[0x1F,0x20,0x40,0x20,0x1F],
        'W':[0x3F,0x40,0x38,0x40,0x3F],'X':[0x63,0x14,0x08,0x14,0x63],
        'Y':[0x07,0x08,0x70,0x08,0x07],'Z':[0x61,0x51,0x49,0x45,0x43],
        '0':[0x3E,0x51,0x49,0x45,0x3E],'1':[0x00,0x42,0x7F,0x40,0x00],
        ' ': [0]*5, '.':[0x00,0x60,0x60,0x00,0x00],
        '!':[0x00,0x00,0x5F,0x00,0x00],':':[0x00,0x36,0x36,0x00,0x00],
        '-':[0x08]*5, '/':[0x20,0x10,0x08,0x04,0x02],
    }
    gl = F.get(ch, F[' '])
    for col in range(5):
        for row in range(7):
            if gl[col] & (1 << row):
                pixel(bw, rd, x+col, y+row, b, r)

def text(bw, rd, x, y, s, b=0, r=0):
    cx = x
    for ch in s:
        if cx + 6 > W: cx = x; y += 9
        char(bw, rd, cx, y, ch, b, r)
        cx += 6

def update(bw, rd):
    print("  Writing B&W RAM...")
    cmd(0x24); data(bw)
    print("  Writing RED RAM...")
    cmd(0x26); data(rd)
    print("  Refreshing (~15s)...")
    cmd(0x22); data(b'\xF4')
    cmd(0x20)
    wait()
    print("  Done!")

# ── Tests ──────────────────────────────────────────────────────
print("\n=== Test 1: Color Bars ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
fill_rect(bw, rd, 0, 0, W, 50, 0, 0)
fill_rect(bw, rd, 0, 50, W, 50, 1, 0)
text(bw, rd, 4, 114, "BLACK BAR", 1, 0)
text(bw, rd, 4, 150, "RED BAR", 1, 0)
update(bw, rd)

print("\n=== Test 2: Checkerboard ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
sz = 16
for row in range(H//sz):
    for col in range(W//sz):
        fill_rect(bw, rd, col*sz, row*sz, sz, sz, (row+col)%2, 0)
update(bw, rd)

print("\n=== Test 3: Borders ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
rect(bw, rd, 0, 0, W, H, 0, 0)
rect(bw, rd, 3, 3, W-6, H-6, 0, 1)
text(bw, rd, 8, 130, "WIRING OK!", 0, 0)
text(bw, rd, 8, 142, "PID 1028", 0, 0)
text(bw, rd, 8, 154, "SSD1680 DIRECT", 0, 1)
update(bw, rd)

print("\n=== Test 4: Characters ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
text(bw, rd, 2, 2, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 0, 0)
text(bw, rd, 2, 14, "0123456789.-/!:TEST", 0, 1)
text(bw, rd, 2, 28, "ALTOID EINK READER", 0, 0)
text(bw, rd, 2, 42, "GP2:SCK GP3:MOSI", 0, 0)
text(bw, rd, 2, 54, "GP5:ECS GP6:D/C", 0, 0)
text(bw, rd, 2, 66, "GP7:RST GP8:BUSY", 0, 0)
rect(bw, rd, 0, 0, W, H, 0, 0)
update(bw, rd)

print("\n=== Test 5: Grid ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
for y in range(0, H, 20):
    fill_rect(bw, rd, 0, y, W, 1, 0, 0)
for x in range(0, W, 20):
    fill_rect(bw, rd, x, 0, 1, H, 0, 0)
text(bw, rd, 10, 270, "GRID PASSED!", 0, 1)
update(bw, rd)

print("\n=== ALL DONE ===")
