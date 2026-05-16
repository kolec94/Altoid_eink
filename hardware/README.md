# Altoid eInk Reader — Hardware Design

## Overview
Battery-powered eInk reader in an Altoids tin enclosure.
Raspberry Pi Pico reads `.txt` files from microSD card on
an Adafruit eInk Breakout Friend (PID 4224) driving a
2.9" tri-color eInk panel (SSD1680). Navigation via 3 buttons.
Powered by Pimoroni Pico LiPo SHIM with LiPo battery.

## Bill of Materials

| Ref | Qty | Part | Notes |
|-----|-----|------|-------|
| U1 | 1 | Raspberry Pi Pico | RP2040, 40-pin DIP |
| U2 | 1 | eInk Breakout Friend (32KB SRAM) | [PID 4224](https://www.adafruit.com/product/4224), SSD1680 driver, SRAM, microSD slot |
| — | 1 | 2.9″ Tri-Color eInk Panel | 128×296, Red/Black/White, 24-pin FPC to Breakout Friend |
| U3 | 1 | Pimoroni Pico LiPo SHIM | PIM557, MCP73831 charger |
| SW1–3 | 3 | Tactile switch, SPST-NO | 6mm, for navigation |
| BAT | 1 | LiPo battery, 3.7V | 500–2000mAh, JST-PH 2-pin |
| — | 1 | JST-PH 2-pin connector | Mates with battery |

## Netlist / Connections

### Pico → Breakout Friend (SPI0 + control)

```
Pico Pin   GPIO    Signal     Breakout Friend Pin
───────   ────    ──────     ──────────────────
  4        GP2     SCK       SCK
  5        GP3     MOSI      MOSI
  6        GP4     MISO      MISO
  7        GP5     ECS       ECS
  9        GP6     D/C       D/C
 10        GP7     RST       RST
 11        GP8     BUSY      BUSY
 12        GP9     SDCS      SDCS
 17        GP13    SRCS      SRCS (hold HIGH!)
 36       3V3(OUT) VIN       VIN
 38       GND      GND       GND
```

⚠️ **SRCS (pin 11 on Breakout Friend) must be connected to GP13 and held HIGH.**  
If left floating, the onboard 32KB SRAM chip randomly activates and corrupts the SPI bus.

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

## Breakout Friend Pinout (PID 4224)

```
  ┌────────────────────────────┐
  │  1  VIN    ○               │
  │  2  GND    ○               │
  │  3  SCK    ○               │
  │  4  MOSI   ○               │
  │  5  MISO   ○               │
  │  6  ECS    ○               │
  │  7  D/C    ○               │
  │  8  RST    ○               │
  │  9  BUSY   ○               │
  │ 10  SDCS   ○               │
  │ 11  SRCS   ○ ← MUST connect!│
  └────────────────────────────┘
        │
  24-pin FPC to eInk panel

Onboard: 32KB SPI SRAM (e.g., 23LC1024), microSD slot
```

## Layout Considerations (Altoids Tin)

Target enclosure: standard Altoids tin (~95×60×20mm internal)

### Stackup (bottom to top):
1. Altoids tin floor (insulated with kapton tape)
2. LiPo battery (500–800mAh for fit)
3. Pico + LiPo SHIM (mounted flat or on side)
4. Breakout Friend + eInk panel (display facing up, through lid cutout)
5. Altoids tin lid (cutout for display, holes for buttons)

### Critical dimensions:
- eInk panel: ~29×67mm (display area)
- Breakout Friend PCB: ~47×37mm
- Pico: 51×21mm
- LiPo SHIM: ~52×21mm (sits under Pico)
- Total stack height: ~12mm (battery 6mm + Pico 5mm + clearance)

Display cutout: ~31×69mm centered on lid
Button holes: 3× 7mm holes along bottom edge of tin

## Schematic Notes for PCB Designer

- The LiPo SHIM is a THT module that solders UNDER the Pico
  (no separate symbol needed — treat Pico+SHIM as one unit)
- Breakout Friend connects via 11-pin female header (2.54mm pitch)
  or direct soldered wires
- SRCS pin MUST be connected — do not leave floating
- eInk panel connects to Breakout Friend via 24-pin FPC (0.5mm pitch)
- Buttons are panel-mount (soldered to perfboard or small PCB)
- Battery connects to SHIM's JST-PH connector

## References
- Pico datasheet: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- Breakout Friend: https://www.adafruit.com/product/4224
- LiPo SHIM: https://shop.pimoroni.com/products/pico-lipo-shim
- SSD1680 datasheet: https://cdn-learn.adafruit.com/assets/assets/000/131/641/original/SSD1680.pdf
