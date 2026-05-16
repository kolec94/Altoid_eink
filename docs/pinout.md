# Altoid eInk Reader — Pin Mapping

## Components
- **MCU:** Raspberry Pi Pico (RP2040)
- **Display driver:** Adafruit eInk Breakout Friend with 32KB SRAM (PID 4224)
- **Display panel:** 2.9″ Tri-Color eInk (SSD1680, 128×296, Red/Black/White)
- **Power:** Pimoroni Pico LiPo SHIM (PIM557)
- **Input:** 3× tactile buttons
- **Battery:** LiPo 3.7V via JST-PH

## Pico ↔ Breakout Friend (SPI0)

| Pico Pin | GPIO | Breakout Friend | Signal |
|----------|------|----------------|--------|
| 4 | GP2 (SPI0 SCK) | SCK | SPI clock |
| 5 | GP3 (SPI0 TX) | MOSI | SPI data, Pico→Display |
| 6 | GP4 (SPI0 RX) | MISO | SPI data, Display→Pico |
| 7 | GP5 | ECS | E-Ink chip select |
| 9 | GP6 | D/C | Data/Command select |
| 10 | GP7 | RST | Hardware reset |
| 11 | GP8 | BUSY | Display busy flag (input) |
| 12 | GP9 | SDCS | SD card chip select |
| **17** | **GP13** | **SRCS** | **SRAM chip select (hold HIGH to disable)** |
| 36 | 3V3(OUT) | VIN | 3.3V power |
| 38 | GND | GND | Ground |

> ⚠️ **SRCS must be connected!** If left floating, the SRAM chip randomly activates and corrupts the SPI bus, resulting in a blank screen. Connect to GP13 (or any unused GPIO) and hold HIGH.

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

## Breakout Friend Pinout (PID 4224)

```
  ┌────────────────────────────┐
  │  1  VIN    ○  │  Power (3.3V)        │
  │  2  GND    ○  │  Ground              │
  │  3  SCK    ○  │  SPI Clock           │
  │  4  MOSI   ○  │  SPI Data In         │
  │  5  MISO   ○  │  SPI Data Out        │
  │  6  ECS    ○  │  E-Ink Chip Select   │
  │  7  D/C    ○  │  Data/Command        │
  │  8  RST    ○  │  Reset               │
  │  9  BUSY   ○  │  Busy Indicator      │
  │ 10  SDCS   ○  │  SD Card Chip Select │
  │ 11  SRCS   ○  │  SRAM Chip Select    │
  └────────────────────────────┘
             │
   24-pin FPC to eInk panel
```

## Display Specs

| Parameter | Value |
|-----------|-------|
| Driver IC | SSD1680 |
| Resolution | 128 × 296 (portrait) |
| Colors | Black, White, Red |
| Interface | 4-wire SPI |
| Onboard SRAM | 32KB (23LC1024 or similar) |
| Update time | ~15s (full refresh) |
| SD card slot | microSD, SPI mode |
