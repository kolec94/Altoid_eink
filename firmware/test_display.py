"""
SRAM-bridge test — CORRECTED pinout for Breakout Friend (4224)
Pins: VIN 3V3 GND SCK MISO MOSI ECS D/C SRCS RST BUSY ENA
"""

from machine import Pin, SPI
from time import sleep_ms

# ── CORRECT PINOUT (read from board silkscreen) ──────────────
PIN_SCK  = 2
PIN_MOSI = 3    # Breakout Friend pin 6 = MOSI → Pico GP3
PIN_MISO = 4    # Breakout Friend pin 5 = MISO → Pico GP4 (unused here but required)
PIN_ECS  = 5    # Breakout Friend pin 7 = ECS
PIN_DC   = 6    # Breakout Friend pin 8 = D/C
PIN_RST  = 7    # Breakout Friend pin 10 = RST
PIN_BUSY = 8    # Breakout Friend pin 11 = BUSY
PIN_SRCS = 13   # Breakout Friend pin 9 = SRCS
PIN_ENA  = 14   # Breakout Friend pin 12 = ENA (display power enable!)

W, H = 128, 296
BE = 16
BS = BE * H

spi = SPI(0, baudrate=4_000_000, sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))
ecs  = Pin(PIN_ECS,  Pin.OUT, value=1)
dc   = Pin(PIN_DC,   Pin.OUT, value=0)
rst  = Pin(PIN_RST,  Pin.OUT, value=1)
busy = Pin(PIN_BUSY, Pin.IN)
srcs = Pin(PIN_SRCS, Pin.OUT, value=1)
ena  = Pin(PIN_ENA,  Pin.OUT, value=1)  # ENABLE display power — must be HIGH

def cmd(c):
    ecs(0); dc(0); spi.write(bytes([c])); ecs(1)

def data(b):
    ecs(0); dc(1); spi.write(b); ecs(1)

def wait(msg=""):
    t = 0
    while busy():
        sleep_ms(10); t += 10
        if t > 30000: raise Exception("BUSY: " + msg)
    if msg: print("  BUSY ok —", msg)

# ── Init ───────────────────────────────────────────────────
print("Power ENA HIGH...")
ena(1)
sleep_ms(10)

print("Init SRAM...")
srcs(0); spi.write(b'\x01\x43'); srcs(1)

print("HW reset...")
rst(1); sleep_ms(100)
rst(0); sleep_ms(100)
rst(1); sleep_ms(200)
wait("hw reset")

print("SW reset...")
cmd(0x12)
wait("sw reset")

print("Init registers...")
cmd(0x01); data(b'\x27\x01\x00')
cmd(0x11); data(b'\x03')
cmd(0x2C); data(b'\x36')
cmd(0x03); data(b'\x17')
cmd(0x04); data(b'\x41\x00\x32')
cmd(0x44); data(b'\x00\x0F')
cmd(0x45); data(b'\x00\x00\x27\x01')
cmd(0x3C); data(b'\x05')
cmd(0x18); data(b'\x80')
cmd(0x4E); data(b'\x00')
cmd(0x4F); data(b'\x00\x00')
wait("init done")
print("Ready!")

# ── SRAM bridge update ─────────────────────────────────────
def update(bw_buf, red_buf):
    # Write to SRAM
    srcs(0)
    spi.write(bytearray([0x02, 0x00, 0x00]))
    spi.write(bw_buf)
    srcs(1)

    srcs(0)
    spi.write(bytearray([0x02, (BS >> 8) & 0xFF, BS & 0xFF]))
    spi.write(red_buf)
    srcs(1)

    # Stream SRAM → B&W RAM
    srcs(0)
    spi.write(bytearray([0x03, 0x00, 0x00]))
    ecs(0); dc(0); spi.write(b'\x24'); dc(1)
    db = 0
    for _ in range(BS):
        spi.write(bytes([db]))
        db = spi.read(1)[0]
    spi.write(bytes([db]))
    ecs(1)

    # Stream SRAM → RED RAM
    srcs(0)
    spi.write(bytearray([0x03, (BS>>8)&0xFF, BS&0xFF]))
    ecs(0); dc(0); spi.write(b'\x26'); dc(1)
    db = 0
    for _ in range(BS):
        spi.write(bytes([db]))
        db = spi.read(1)[0]
    spi.write(bytes([db]))
    ecs(1); srcs(1)

    # Refresh
    cmd(0x22); data(b'\xF4')
    cmd(0x20)
    wait("refresh")

# ── Drawing ────────────────────────────────────────────────
def pixel(bw, rd, x, y, b, r):
    if not (0 <= x < W and 0 <= y < H): return
    idx = (y*BE) + (x>>3)
    m = 0x80 >> (x&7)
    if b: bw[idx] |= m
    else: bw[idx] &= ~m
    if r: rd[idx] |= m
    else: rd[idx] &= ~m

def fill(bw, rd, x, y, w, h, b, r):
    for dy in range(h):
        for dx in range(w): pixel(bw, rd, x+dx, y+dy, b, r)

def rect(bw, rd, x, y, w, h, b, r):
    fill(bw, rd, x, y, w, 1, b, r)
    fill(bw, rd, x, y+h-1, w, 1, b, r)
    fill(bw, rd, x, y, 1, h, b, r)
    fill(bw, rd, x+w-1, y, 1, h, b, r)

F = {'A':[0x7E,0x11,0x11,0x11,0x7E],'B':[0x7F,0x49,0x49,0x49,0x36],
     'C':[0x3E,0x41,0x41,0x41,0x22],'D':[0x7F,0x41,0x41,0x22,0x1C],
     'E':[0x7F,0x49,0x49,0x49,0x41],'F':[0x7F,0x09,0x09,0x09,0x01],
     'G':[0x3E,0x41,0x49,0x49,0x7A],'H':[0x7F,0x08,0x08,0x08,0x7F],
     'I':[0x00,0x41,0x7F,0x41,0x00],'K':[0x7F,0x08,0x14,0x22,0x41],
     'L':[0x7F,0x40,0x40,0x40,0x40],'M':[0x7F,0x02,0x0C,0x02,0x7F],
     'N':[0x7F,0x04,0x08,0x10,0x7F],'O':[0x3E,0x41,0x41,0x41,0x3E],
     'P':[0x7F,0x09,0x09,0x09,0x06],'R':[0x7F,0x09,0x19,0x29,0x46],
     'S':[0x46,0x49,0x49,0x49,0x31],'T':[0x01,0x01,0x7F,0x01,0x01],
     'U':[0x3F,0x40,0x40,0x40,0x3F],'W':[0x3F,0x40,0x38,0x40,0x3F],
     'X':[0x63,0x14,0x08,0x14,0x63],'Y':[0x07,0x08,0x70,0x08,0x07],
     '0':[0x3E,0x51,0x49,0x45,0x3E],'1':[0x00,0x42,0x7F,0x40,0x00],
     ' ': [0]*5, '.':[0x00,0x60,0x60,0x00,0x00],'!':[0x00,0x00,0x5F,0x00,0x00],
     '-':[0x08]*5}

def chr(bw, rd, x, y, ch, b=0, r=0):
    g = F.get(ch, F[' '])
    for c in range(5):
        for rw in range(7):
            if g[c] & (1<<rw): pixel(bw, rd, x+c, y+rw, b, r)

def txt(bw, rd, x, y, s, b=0, r=0):
    cx = x
    for ch in s:
        if cx+6 > W: cx = x; y += 9
        chr(bw, rd, cx, y, ch, b, r)
        cx += 6

# ── Tests ──────────────────────────────────────────────────
print("\n=== Test 1/3: Color Bars ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
fill(bw, rd, 0, 0, W, 50, 0, 0)
fill(bw, rd, 0, 50, W, 50, 1, 0)
txt(bw, rd, 4, 114, "BLACK", 1, 0)
txt(bw, rd, 4, 150, "RED", 1, 0)
txt(bw, rd, 4, 200, "PINOUT FIXED!", 0, 0)
update(bw, rd)

print("\n=== Test 2/3: Borders + Text ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
rect(bw, rd, 0, 0, W, H, 0, 0)
rect(bw, rd, 3, 3, W-6, H-6, 0, 1)
txt(bw, rd, 8, 120, "WIRING CORRECT!", 0, 0)
txt(bw, rd, 8, 135, "4224 BREAKOUT", 0, 0)
txt(bw, rd, 8, 150, "ENA PIN ACTIVE", 0, 1)
update(bw, rd)

print("\n=== Test 3/3: Grid ===")
bw = bytearray([0xFF]*BS); rd = bytearray([0xFF]*BS)
for y in range(0, H, 20): fill(bw, rd, 0, y, W, 1, 0, 0)
for x in range(0, W, 20): fill(bw, rd, x, 0, 1, H, 0, 0)
txt(bw, rd, 6, 270, "GRID PASSED!", 0, 1)
update(bw, rd)

print("\n=== ALL TESTS DONE ===")
