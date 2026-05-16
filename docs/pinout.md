# Altoid eInk Reader — Pin Mapping

## Components
- **MCU:** Raspberry Pi Pico (RP2040)
- **Display:** Adafruit 2.9" Tri-Color eInk Breakout (SSD1680, 128×296)
- **Power:** Pimoroni Pico LiPo SHIM (PIM557)
- **Input:** 3× tactile buttons
- **Battery:** LiPo 3.7V via JST-PH

## Pico ↔ eInk Breakout (SPI0)

| Pico Pin | GPIO | Breakout Pin | Signal |
|----------|------|-------------|--------|
| 4 | GP2 (SPI0 SCK) | SCK | SPI clock |
| 5 | GP3 (SPI0 TX) | MOSI | SPI data, Pico→Display |
| 6 | GP4 (SPI0 RX) | MISO | SPI data, SD→Pico |
| 7 | GP5 | ECS | E-Ink chip select |
| 9 | GP6 | D/C | Data/Command select |
| 10 | GP7 | RST | Hardware reset |
| 11 | GP8 | BUSY | Display busy flag (input) |
| 12 | GP9 | SDCS | SD card chip select |
| 36 | 3V3(OUT) | VIN | 3.3V power |
| 38 | GND | GND | Ground |

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
| Interface | 4-wire SPI |
| Update time | ~15s (full refresh) |
| SD card slot | microSD, SPI mode |
