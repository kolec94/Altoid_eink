# Altoid eInk Reader — Hardware Design

## Overview
Battery-powered eInk reader in an Altoids tin enclosure.
Raspberry Pi Pico reads `.txt` files from a microSD card on an
Adafruit 2.9" Red/Black/White ThinkInk display (PID 1028, SSD1680).
The display connects through its 18-pin EYESPI connector using an
Adafruit EYESPI Breakout Board (PID 5613). Navigation via 3 buttons.
Powered by Pimoroni Pico LiPo SHIM with LiPo battery.

## Bill of Materials

| Ref | Qty | Part | Notes |
|-----|-----|------|-------|
| U1 | 1 | Raspberry Pi Pico | RP2040, 40-pin DIP |
| U2 | 1 | Adafruit 2.9" ThinkInk Tri-Color eInk Display | [PID 1028](https://www.adafruit.com/product/1028), SSD1680, onboard SRAM, microSD, EYESPI |
| J1 | 1 | EYESPI Breakout Board | [PID 5613](https://www.adafruit.com/product/5613), 18-pin FPC to breadboard/header pins |
| — | 1 | 18-pin EYESPI cable | EYESPI A-B cable |
| U3 | 1 | Pimoroni Pico LiPo SHIM | PIM557, MCP73831 charger |
| SW1–3 | 3 | Tactile switch, SPST-NO | 6mm, for navigation |
| BAT | 1 | LiPo battery, 3.7V | 500–2000mAh, JST-PH 2-pin |
| — | 1 | JST-PH 2-pin connector | Mates with battery |

## Netlist / Connections

### Pico → EYESPI Breakout (SPI0 + control)

Wire to the signal labels printed on the EYESPI breakout adapter.

```
EYESPI Label   Pico Pin   GPIO / Power   Function
────────────   ────────   ────────────   ────────
VIN            36         3V3(OUT)       Power
GND            38         GND            Ground
SCK             4         GP2            SPI clock
MOSI            5         GP3            SPI data out
MISO            6         GP4            SPI data in
TCS             7         GP5            eInk chip select
DC              9         GP6            Data/command
RST            10         GP7            Reset
BUSY           11         GP8            Busy indicator
SDCS           12         GP9            SD card chip select
MEMCS          17         GP13           SRAM/memory chip select
```

There is no `ENA` wire in this EYESPI setup.

### Pico → Buttons

```
 14       GP10     BTN_UP     SW1 → GND
 15       GP11     BTN_DOWN   SW2 → GND
 16       GP12     BTN_SEL    SW3 → GND
```

Buttons are active low (GPIO pulled up internally, button connects to GND).
No external pull-up resistors needed — Pico internal pull-ups are used.

### Power (LiPo SHIM)

Pimoroni Pico LiPo SHIM solders directly to Pico castellations:
- VBUS, VSYS, GND, 3V3_EN pads on back of Pico
- Provides MCP73831 LiPo charger (charges when USB connected)
- Physical power switch
- Battery JST-PH connector on SHIM

Battery monitoring: Pico ADC3 (GP29) reads VSYS/3 internally.
No extra pin needed.

## EYESPI Connection

```
Pico GPIO/header wires
        │
        ▼
Adafruit EYESPI Breakout Board (PID 5613)
        │
        ▼
18-pin EYESPI FPC cable
        │
        ▼
Adafruit 2.9" ThinkInk Display (PID 1028)
```

Use an 18-pin 0.5mm EYESPI cable. Raspberry Pi camera cables are not compatible.

## Layout Considerations (Altoids Tin)

Target enclosure: standard Altoids tin (~95×60×20mm internal)

### Stackup (bottom to top):
1. Altoids tin floor (insulated with kapton tape)
2. LiPo battery (500–800mAh for fit)
3. Pico + LiPo SHIM (mounted flat or on side)
4. EYESPI breakout adapter and cable routing
5. ThinkInk display mounted to the inside of the lid, screen facing into the tin
6. Altoids tin lid (unopened top surface, no display cutout)

### Critical dimensions:
- eInk display active area: 2.9", 128×296
- Pico: 51×21mm
- LiPo SHIM: ~52×21mm (sits under Pico)
- EYESPI breakout: ~25×18mm

Display opening: none — screen is viewed when the lid is open
Button holes: 3× 7mm holes along bottom edge of tin

## Schematic Notes for PCB Designer

- Treat the ThinkInk display as an EYESPI-connected module.
- Use the EYESPI labels `TCS`, `MEMCS`, and `SDCS` in the schematic and firmware.
- The LiPo SHIM is a THT module that solders UNDER the Pico.
- Buttons are panel-mount (soldered to perfboard or small PCB).
- Battery connects to SHIM's JST-PH connector.

## References
- Pico datasheet: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- ThinkInk 2.9" display: https://www.adafruit.com/product/1028
- EYESPI breakout: https://www.adafruit.com/product/5613
- LiPo SHIM: https://shop.pimoroni.com/products/pico-lipo-shim
- SSD1680 datasheet: https://cdn-learn.adafruit.com/assets/assets/000/131/641/original/SSD1680.pdf
