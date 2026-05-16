# Altoid eInk Reader — Pin Mapping

## Components
- **MCU:** Raspberry Pi Pico (RP2040)
- **Display:** Adafruit 2.9" Red/Black/White eInk Display Breakout - THINK INK (SSD1680, PID 1028)
- **Connection:** 18-pin EYESPI cable plus Adafruit EYESPI Breakout Board (PID 5613)
- **Power:** Pimoroni Pico LiPo SHIM (PIM557)
- **Input:** 3× tactile buttons
- **Battery:** LiPo 3.7V via JST-PH

## EYESPI Breakout Wiring

Wire to the signal labels printed on the EYESPI breakout board.

```
EYESPI Label   Description             Pico GPIO / Power   Pico Pin
────────────   ───────────             ─────────────────   ────────
VIN            Power                   3V3(OUT)             36
GND            Ground                  GND                  38
SCK            SPI Clock               GP2                   4
MOSI           SPI Data Out            GP3                   5
MISO           SPI Data In             GP4                   6
TCS            eInk Chip Select        GP5                   7
DC             Data/Command            GP6                   9
RST            Hardware Reset          GP7                  10
BUSY           Busy Indicator          GP8                  11
SDCS           SD Card Chip Select     GP9                  12
MEMCS          SRAM Chip Select        GP13                 17
```

There is no `ENA` wire in this EYESPI setup.

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
| Interface | 4-wire SPI via EYESPI |
| Onboard SRAM | Controlled by `MEMCS` |
| Update time | ~15s (full refresh) |
| SD card | Controlled by `SDCS` |
