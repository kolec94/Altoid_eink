# Altoid eInk Reader — Hardware Design

## Overview
Battery-powered eInk reader in an Altoids tin enclosure.
Raspberry Pi Pico reads `.txt` files from microSD card on
Adafruit 2.9" tri-color eInk breakout. Navigation via 3 buttons.
Powered by Pimoroni Pico LiPo SHIM with LiPo battery.

## Bill of Materials

| Ref | Qty | Part | Notes |
|-----|-----|------|-------|
| U1 | 1 | Raspberry Pi Pico | RP2040, 40-pin DIP |
| U2 | 1 | Adafruit 2.9" Tri-Color eInk Breakout | PID 1028, SSD1680, 128×296, microSD slot |
| U3 | 1 | Pimoroni Pico LiPo SHIM | PIM557, MCP73831 charger |
| SW1–3 | 3 | Tactile switch, SPST-NO | 6mm, for navigation |
| BAT | 1 | LiPo battery, 3.7V | 500–2000mAh, JST-PH 2-pin |
| — | 1 | JST-PH 2-pin connector | Mates with battery |

## Netlist / Connections

### Pico → eInk Breakout (SPI0 + control)

```
Pico Pin   GPIO    Signal    Breakout Pin
───────   ────    ──────    ────────────
  4        GP2     SCK      SCK
  5        GP3     MOSI     MOSI
  6        GP4     MISO     MISO
  7        GP5     ECS      ECS
  9        GP6     D/C      D/C
 10        GP7     RST      RST
 11        GP8     BUSY     BUSY
 12        GP9     SDCS     SDCS
 36       3V3(OUT) VIN     VIN
 38       GND      GND     GND
```

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

## Layout Considerations (Altoids Tin)

Target enclosure: standard Altoids tin (~95×60×20mm internal)

### Stackup (bottom to top):
1. Altoids tin floor (insulated with kapton tape)
2. LiPo battery (500–800mAh for fit)
3. Pico + LiPo SHIM (mounted flat or on side)
4. eInk breakout (display facing up, through lid cutout)
5. Altoids tin lid (cutout for display, holes for buttons)

### Critical dimensions:
- eInk PCB: ~47×40mm (display area: 29×67mm)
- Pico: 51×21mm
- LiPo SHIM: ~52×21mm (sits under Pico)
- Total stack height: ~12mm (battery 6mm + Pico 5mm + clearance)

Display cutout: ~31×69mm centered on lid
Button holes: 3× 7mm holes along bottom edge of tin

## Schematic Notes for PCB Designer

- The LiPo SHIM is a THT module that solders UNDER the Pico
  (no separate symbol needed — treat Pico+SHIM as one unit)
- eInk breakout connects via 10-pin female header (2.54mm pitch)
  or direct soldered wires
- Buttons are panel-mount (soldered to perfboard or small PCB)
- Battery connects to SHIM's JST-PH connector
- Consider a small perfboard or custom PCB to mount buttons
  and route connections cleanly

## References
- Pico datasheet: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- eInk breakout: https://www.adafruit.com/product/1028
- LiPo SHIM: https://shop.pimoroni.com/products/pico-lipo-shim
- SSD1680 datasheet: https://cdn-learn.adafruit.com/assets/assets/000/131/641/original/SSD1680.pdf
