#!/usr/bin/env python3
"""
KiCad Schematic Generator — Altoid eInk Reader
===============================================
Generates Altoid_eink.kicad_sch in KiCad 8 S-expression format.

Usage:
    python3 generate_schematic.py

Outputs: hardware/Altoid_eink.kicad_sch

Requirements for the target machine:
    - KiCad 7 or 8 standard symbol libraries installed
      (MCU_RaspberryPi, Connector, Switch, Device)
"""

import uuid
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Altoid_eink.kicad_sch")

# ── UUIDs (deterministic-ish for reproducibility) ────────────────
# Generate fresh UUIDs each run (or keep same for version control)

def fresh_uuid():
    return str(uuid.uuid4())

SCH_UUID = fresh_uuid()

# Symbol UUIDs
PICO_UUID   = fresh_uuid()
EINK_UUID   = fresh_uuid()
BTN_UP_UUID   = fresh_uuid()
BTN_DOWN_UUID = fresh_uuid()
BTN_SEL_UUID  = fresh_uuid()

# Pin UUIDs for Pico (40 pins)
pico_pin_uuids = [fresh_uuid() for _ in range(40)]

# Pin UUIDs for eInk connector
eink_pin_uuids = [fresh_uuid() for _ in range(10)]

# Pin UUIDs for buttons
btn_up_pin   = [fresh_uuid() for _ in range(2)]
btn_down_pin = [fresh_uuid() for _ in range(2)]
btn_sel_pin  = [fresh_uuid() for _ in range(2)]

# ── Helper: generate a symbol node ──────────────────────────────

def make_pico_symbol(at_x=50, at_y=100):
    """Raspberry Pi Pico symbol (40 pins)."""
    lines = []
    lines.append(f'    (symbol (lib_id "MCU_RaspberryPi:RPi_Pico") (at {at_x} {at_y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)')
    lines.append(f'      (uuid "{PICO_UUID}")')
    lines.append(f'      (property "Reference" "U1" (at {at_x} {at_y - 55} 0) (effects (font (size 1.27 1.27))) )')
    lines.append(f'      (property "Value" "Raspberry_Pi_Pico" (at {at_x} {at_y + 55} 0) (effects (font (size 1.27 1.27))) )')
    lines.append(f'      (property "Footprint" "MCU_RaspberryPi:RPi_Pico_TH" (at {at_x} {at_y} 0) (effects (font (size 1.27 1.27)) hide) )')
    lines.append(f'      (property "Datasheet" "https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf" (at {at_x} {at_y} 0) (effects (font (size 1.27 1.27)) hide) )')

    # Pico pin names
    pin_names = [
        "GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND",
        "GP6", "GP7", "GP8", "GP9", "GND", "GP10", "GP11", "GP12",
        "GP13", "GND", "GP14", "GP15", "GP16", "GP17", "GND", "GP18",
        "GP19", "GP20", "GP21", "GND", "GP22", "RUN", "GP26_ADC0",
        "GP27_ADC1", "GND/AGND", "GP28_ADC2", "ADC_VREF", "3V3(OUT)",
        "3V3_EN", "GND", "VSYS", "VBUS"
    ]
    for i, name in enumerate(pin_names):
        lines.append(f'      (pin "{name}" (uuid "{pico_pin_uuids[i]}"))')

    lines.append('    )')
    return '\n'.join(lines)


def make_eink_connector(at_x=150, at_y=100):
    """10-pin connector for Adafruit eInk breakout."""
    pin_names = ["VIN", "GND", "SCK", "MOSI", "MISO",
                 "ECS", "D/C", "RST", "BUSY", "SDCS"]

    lines = []
    lines.append(f'    (symbol (lib_id "Connector:Conn_01x10_Female") (at {at_x} {at_y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)')
    lines.append(f'      (uuid "{EINK_UUID}")')
    lines.append(f'      (property "Reference" "J1" (at {at_x - 6} {at_y - 30} 0) (effects (font (size 1.27 1.27))) )')
    lines.append(f'      (property "Value" "eInk_Breakout" (at {at_x + 4} {at_y - 30} 0) (effects (font (size 1.27 1.27))) )')
    lines.append(f'      (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical" (at {at_x} {at_y} 0) (effects (font (size 1.27 1.27)) hide) )')
    lines.append(f'      (property "Datasheet" "https://www.adafruit.com/product/1028" (at {at_x} {at_y} 0) (effects (font (size 1.27 1.27)) hide) )')

    for i, name in enumerate(pin_names):
        lines.append(f'      (pin "{name}" (uuid "{eink_pin_uuids[i]}"))')

    lines.append('    )')
    return '\n'.join(lines)


def make_button(prefix, ref, uuid_val, at_x, at_y):
    """Tactile push button symbol."""
    pin_uuids = [fresh_uuid() for _ in range(2)]
    lines = []
    lines.append(f'    (symbol (lib_id "Switch:SW_Push") (at {at_x} {at_y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)')
    lines.append(f'      (uuid "{uuid_val}")')
    lines.append(f'      (property "Reference" "{ref}" (at {at_x} {at_y + 6} 0) (effects (font (size 1.27 1.27))) )')
    lines.append(f'      (property "Value" "{prefix}" (at {at_x} {at_y - 6} 0) (effects (font (size 1.27 1.27))) )')
    lines.append(f'      (property "Footprint" "Button_Switch_THT:SW_PUSH_6mm" (at {at_x} {at_y} 0) (effects (font (size 1.27 1.27)) hide) )')
    lines.append(f'      (pin "1" (uuid "{pin_uuids[0]}"))')
    lines.append(f'      (pin "2" (uuid "{pin_uuids[1]}"))')
    lines.append('    )')
    return '\n'.join(lines)


def make_wire(uuid_val, start_x, start_y, end_x, end_y):
    """Wire segment."""
    return f'    (wire (pts (xy {start_x} {start_y}) (xy {end_x} {end_y})) (stroke (width 0) (type default)) (uuid "{uuid_val}"))'


def make_label(text, x, y, orientation=0):
    """Net label."""
    return f'    (label "{text}" (at {x} {y} {orientation}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{fresh_uuid()}"))'


# ── Main generation ─────────────────────────────────────────────

def generate():
    schematic = []

    # Header
    schematic.append(f'(kicad_sch (version 20231120) (generator "generate_schematic.py")')
    schematic.append(f'  (uuid "{SCH_UUID}")')
    schematic.append(f'')
    schematic.append(f'  (paper "A4")')
    schematic.append(f'')
    schematic.append(f'  (title_block')
    schematic.append(f'    (title "Altoid eInk Reader")')
    schematic.append(f'    (date "2026-05-16")')
    schematic.append(f'    (rev "0.1")')
    schematic.append(f'    (company "")')
    schematic.append(f'  )')
    schematic.append(f'')

    # Lib symbols (empty - using system libs)
    schematic.append(f'  (lib_symbols)')
    schematic.append(f'')

    # Sheet
    sheet_uuid = fresh_uuid()
    schematic.append(f'  (sheet (at 0 0) (size 150 100) (fields_autoplaced)')
    schematic.append(f'    (uuid "{sheet_uuid}")')
    schematic.append(f'    (property "Sheet name" "Root" (at 0 0 0) (effects (font (size 1.27 1.27))) )')
    schematic.append(f'    (property "Sheet file" "Altoid_eink.kicad_sch" (at 0 0 0) (effects (font (size 1.27 1.27))) )')
    schematic.append(f'')

    # ── Symbols ─────────────────────────────────────────────────
    # Pico at left side
    pico_x, pico_y = 50, 100
    schematic.append(make_pico_symbol(pico_x, pico_y))
    schematic.append('')

    # eInk connector at right side
    eink_x, eink_y = 200, 100
    schematic.append(make_eink_connector(eink_x, eink_y))
    schematic.append('')

    # Buttons at bottom
    btn_y = 180
    schematic.append(make_button("BTN_UP",   "SW1", BTN_UP_UUID,   50, btn_y))
    schematic.append(make_button("BTN_DOWN", "SW2", BTN_DOWN_UUID, 100, btn_y))
    schematic.append(make_button("BTN_SEL",  "SW3", BTN_SEL_UUID,  150, btn_y))
    schematic.append('')

    # ── Wires (drawn as straight lines between component pins) ──
    # Pico pins are laid out: left column (odd pins: 1,3,5...39) on left,
    # right column (even pins: 2,4,6...40) on right
    # Pin mapping for Pico (pins are 0-indexed in pico_pin_uuids):
    #   index 0=GP0(pin1), 1=GP1(pin2), 2=GND(pin3), 3=GP2(pin4), ...

    # eInk connection wires: Pico right-side pins → eInk left-side pins
    # Pico pin positions (x offset from pico_x):
    #   Left pins:  pico_x - 13
    #   Right pins: pico_x + 13
    # Pin Y spacing: ~2.54mm per pin in KiCad units (100 mil = 2.54)

    # eInk pins (left side): eink_x - 5, Y spaced 2.54mm
    # We'll draw wires between matching pins

    wire_y_offsets = {
        # Pico pin index, pin name, Pico side, eInk pin index, eInk name
        3:  "GP2_SCK",   # index 3 = GP2 (pin 4)
        4:  "GP3_MOSI",  # index 4 = GP3 (pin 5)
        5:  "GP4_MISO",  # index 5 = GP4 (pin 6)
        6:  "GP5_ECS",   # index 6 = GP5 (pin 7)
        8:  "GP6_DC",    # index 8 = GP6 (pin 9)
        9:  "GP7_RST",   # index 9 = GP7 (pin 10)
        10: "GP8_BUSY",  # index 10 = GP8 (pin 11)
        11: "GP9_SDCS",  # index 11 = GP9 (pin 12)
        # Power pins
        35: "3V3",       # index 35 = 3V3(OUT) pin 36
        37: "GND",       # index 37 = GND pin 38
    }

    # Wires: Pico right side → eInk breakout
    # eInk connector has 10 pins (0-9): VIN, GND, SCK, MOSI, MISO, ECS, D/C, RST, BUSY, SDCS
    # Align with pins 36,38 down through 4-12
    eink_to_pico = {
        0: 35,  # VIN  → 3V3(OUT)
        1: 37,  # GND  → GND
        2: 3,   # SCK  → GP2
        3: 4,   # MOSI → GP3
        4: 5,   # MISO → GP4
        5: 6,   # ECS  → GP5
        6: 8,   # D/C  → GP6
        7: 9,   # RST  → GP7
        8: 10,  # BUSY → GP8
        9: 11,  # SDCS → GP9
    }

    # Pico pin positions (KiCad symbols have standard pin layout)
    # Left column (pins 1,3,5...39): x = -10mm (-400 mils)
    # Right column (pins 2,4,6...40): x = +10mm (+400 mils)
    # Pin 1 at top (y = +52mm), pin spacing = 2.54mm (100 mils)
    #
    # Need to convert pin index to position:
    # Left pins (even indices 0,2,4...38): pin number = index+1
    #   Pin 1 (index 0) at x = pico_x - 10, y = pico_y + 52
    #   Each subsequent pin: y -= 2.54mm
    # Right pins (odd indices 1,3,5...39):
    #   Pin 2 (index 1) at x = pico_x + 10, y = pico_y + 52
    #   Each subsequent pin: y -= 2.54mm

    def pico_pin_pos(index):
        """Return (x, y) in mm for Pico pin at given 0-based index."""
        pin_num = index + 1
        if pin_num % 2 == 1:  # Left side
            x = pico_x - 10
        else:  # Right side
            x = pico_x + 10
        # Pin 1/2 at top
        y = pico_y + (52 - (index // 2) * 2.54)
        return x, y

    def eink_pin_pos(pin_index):
        """Return (x, y) for eInk connector pin (0-9)."""
        # Connector is vertical, pin 1 at top
        x = eink_x - 3  # left side of connector
        y = eink_y + (15 - pin_index * 2.54)  # 10 pins, 2.54mm pitch
        return x, y

    # Draw connection wires
    for eink_idx, pico_idx in eink_to_pico.items():
        # Use net labels instead of direct wires for cleaner schematic
        pico_x_pos, pico_y_pos = pico_pin_pos(pico_idx)
        eink_x_pos, eink_y_pos = eink_pin_pos(eink_idx)

        # Net name based on eInk signal
        eink_pin_names = ["VIN", "GND", "SCK", "MOSI", "MISO",
                          "ECS", "D_C", "RST", "BUSY", "SDCS"]
        net_name = eink_pin_names[eink_idx]

        # Label on Pico side
        schematic.append(make_label(net_name, pico_x_pos + 3, pico_y_pos, 0))
        # Label on eInk side (same net name connects them)
        schematic.append(make_label(net_name, eink_x_pos - 3, eink_y_pos, 2))

    # Button connections
    # Pico pins: GP10 (index 12), GP11 (index 13), GP12 (index 14)
    for btn_idx, (pico_idx, btn_x) in enumerate([(12, 50), (13, 100), (14, 150)]):
        net_name = ["BTN_UP", "BTN_DOWN", "BTN_SEL"][btn_idx]
        px, py = pico_pin_pos(pico_idx)
        # Pico side label
        schematic.append(make_label(net_name, px + 3, py, 0))
        # Button pin 1 (top)
        schematic.append(make_label(net_name, btn_x - 3, btn_y + 4, 2))
        # Button pin 2 (bottom) → GND
        schematic.append(make_label("GND", btn_x - 3, btn_y - 4, 2))

    schematic.append('')
    schematic.append('  )')
    schematic.append(')')

    # Write file
    content = '\n'.join(schematic)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(content)
    print(f"Generated: {OUTPUT_FILE}")
    print(f"  Symbols: 1× Pico, 1× eInk connector, 3× push buttons")
    print(f"  Nets: 10× Pico→eInk (by label), 3× Pico→buttons (by label)")


if __name__ == '__main__':
    generate()
