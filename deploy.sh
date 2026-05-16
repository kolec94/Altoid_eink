#!/bin/bash
# deploy.sh — Flash firmware files to Raspberry Pi Pico
# ======================================================
# Usage: ./deploy.sh [PORT]
#   PORT defaults to /dev/ttyACM0
#
# Prerequisites:
#   1. MicroPython UF2 installed on Pico (RP2040)
#      Download: https://micropython.org/download/RPI_PICO/
#   2. mpremote installed: pip install mpremote
#   3. Or use ampy: pip install adafruit-ampy

set -e

PORT="${1:-/dev/ttyACM0}"
FIRMWARE_DIR="$(dirname "$0")/firmware"
FILES=("main.py" "reader.py" "ssd1680.py" "sdcard.py" "font5x7.py")

echo "=== Altoid eInk Reader — Deploy ==="
echo "Port: $PORT"
echo "Files: ${FILES[*]}"
echo ""

# Check if port exists
if [ ! -e "$PORT" ]; then
    echo "ERROR: $PORT not found."
    echo "Is the Pico connected and running MicroPython?"
    echo ""
    echo "To install MicroPython on Pico:"
    echo "  1. Hold BOOTSEL button on Pico"
    echo "  2. Connect USB cable"
    echo "  3. Pico appears as a USB drive (RPI-RP2)"
    echo "  4. Copy MicroPython .uf2 file to the drive"
    echo "  5. Pico reboots into MicroPython"
    exit 1
fi

# Check for mpremote or ampy
if command -v mpremote &>/dev/null; then
    echo "Using mpremote..."
    for f in "${FILES[@]}"; do
        echo "  Copying $f..."
        mpremote connect "$PORT" fs cp "$FIRMWARE_DIR/$f" ":$f"
    done
    echo ""
    echo "Resetting Pico..."
    mpremote connect "$PORT" reset
    echo "Done! Files deployed."

elif command -v ampy &>/dev/null; then
    echo "Using ampy..."
    for f in "${FILES[@]}"; do
        echo "  Copying $f..."
        ampy -p "$PORT" put "$FIRMWARE_DIR/$f"
    done
    echo "Done! Files deployed. Reset Pico to run."

else
    echo "WARNING: Neither mpremote nor ampy found."
    echo "Install one of them:"
    echo "  pip install mpremote"
    echo "  pip install adafruit-ampy"
    echo ""
    echo "Manual copy:"
    echo "  1. Install Thonny IDE"
    echo "  2. Connect to Pico"
    echo "  3. Copy files from firmware/ to Pico root"
    echo ""
    echo "Files to copy:"
    for f in "${FILES[@]}"; do
        echo "  firmware/$f"
    done
    exit 1
fi
