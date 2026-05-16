# Altoid eInk Reader — Pin Mapping

## Components
- **MCU:** Raspberry Pi Pico (RP2040)
- **Display driver:** Adafruit eInk Breakout Friend with 32KB SRAM (PID 4224)
- **Display panel:** 2.9″ Tri-Color eInk (SSD1680, 128×296, Red/Black/White) via 24-pin FPC
- **Power:** Pimoroni Pico LiPo SHIM (PIM557)
- **Input:** 3× tactile buttons
- **Battery:** LiPo 3.7V via JST-PH

## Breakout Friend 12-Pin Header (read from board silkscreen!)

```
Pin  Label   Description        → Pico GPIO  Pico Pin
───  ─────   ───────────        ──────────  ────────
 1   VIN     Power (3.3-5V)     → 3V3(OUT)   36
 2   3V3     3.3V output        → (unused)
 3   GND     Ground             → GND         38
 4   SCK     SPI Clock          → GP2          4
 5   MISO    SPI Data In        → GP4          6
 6   MOSI    SPI Data Out       → GP3          5
 7   ECS     E-Ink Chip Select  → GP5          7
 8   D/C     Data/Command       → GP6          9
 9   SRCS    SRAM Chip Select   → GP13        17
10   RST     Hardware Reset     → GP7         10
11   BUSY    Busy Indicator     → GP8         11
12   ENA     Display Enable     → GP14        19
```

> ⚠️ **ENA must be connected and held HIGH** — this enables power to the display panel.

## Pico ↔ Buttons

| Pico Pin | GPIO | Button | Function |
|----------|------|--------|----------|
| 14 | GP10 | BTN_UP | Previous page / scroll up |
| 15 | GP11 | BTN_DOWN | Next page / scroll down |
| 16 | GP12 | BTN_SEL | Select / menu |

Buttons wired: GPIO → button → GND. Internal pull-up enabled in firmware.

## Power (Pico LiPo SHIM)

| Connection | Notes |
|-----------|-------|
| LiPo SHIM sits under Pico | Solders to Pico castellations (VBUS, VSYS, GND, 3V3_EN) |
| Battery → LiPo SHIM JST-PH | 3.7V LiPo (500–2000 mAh) |
| SHIM provides | MCP73831 charging (via USB), power switch, VBAT/VSYS steering |
| Battery level | Read via Pico ADC3 (VSYS/3), no extra pin needed |

## Display Specs

| Parameter | Value |
|-----------|-------|
| Driver IC | SSD1680 |
| Resolution | 128 × 296 (portrait) |
| Colors | Black, White, Red |
| Interface | 4-wire SPI (via Breakout Friend SRAM bridge) |
| Onboard SRAM | 32KB (23LC1024 or similar) — used as frame buffer |
| Update time | ~15s (full refresh) |
| SD card slot | On Breakout Friend, SPI mode |
