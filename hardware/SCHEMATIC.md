# Altoid eInk Reader — Schematic

Raspberry Pi Pico wired to an Adafruit 2.9" ThinkInk display (PID 1028) through the 18-pin EYESPI connector and EYESPI breakout adapter (PID 5613).

## System Block Diagram

```mermaid
flowchart LR
    subgraph Pico["🍓 Raspberry Pi Pico"]
        direction LR
        SPI0["SPI0<br/>GP2-4"]
        GP5["GP5 · TCS"]
        GP6["GP6 · DC"]
        GP7["GP7 · RST"]
        GP8["GP8 · BUSY"]
        GP9["GP9 · SDCS"]
        GP13["GP13 · MEMCS"]
        GP10["GP10"]
        GP11["GP11"]
        GP12["GP12"]
        PWR["3V3<br/>GND"]
    end

    subgraph EYESPI["🔌 EYESPI Breakout<br/>(PID 5613)"]
        VIN["VIN"]
        GND_e["GND"]
        SCK["SCK"]
        MOSI["MOSI"]
        MISO["MISO"]
        TCS["TCS"]
        DC["DC"]
        RST["RST"]
        BUSY["BUSY"]
        SDCS["SDCS"]
        MEMCS["MEMCS"]
    end

    Display["🖥️ ThinkInk 2.9″<br/>SSD1680 · PID 1028"]

    subgraph Buttons["🔘 Controls"]
        UP["BTN_UP · SW1"]
        DOWN["BTN_DOWN · SW2"]
        SEL["BTN_SEL · SW3"]
    end

    subgraph Power["🔋 Power"]
        SHIM["Pico LiPo SHIM<br/>MCP73831"]
        BAT["LiPo 3.7V<br/>JST-PH"]
    end

    SPI0 --> SCK
    SPI0 --> MOSI
    SPI0 --> MISO
    GP5 --> TCS
    GP6 --> DC
    GP7 --> RST
    GP8 --> BUSY
    GP9 --> SDCS
    GP13 --> MEMCS
    PWR --> VIN
    PWR --> GND_e
    EYESPI -- "18-pin FPC cable" --> Display
    GP10 --> UP
    GP11 --> DOWN
    GP12 --> SEL
    SHIM -- "solders under Pico" --> Pico
    BAT --> SHIM
```

## Pin Connections

| EYESPI label | Pico pin | GPIO / Power |
|--------------|----------|--------------|
| VIN | 36 | 3V3(OUT) |
| GND | 38 | GND |
| SCK | 4 | GP2 |
| MOSI | 5 | GP3 |
| MISO | 6 | GP4 |
| TCS | 7 | GP5 |
| DC | 9 | GP6 |
| RST | 10 | GP7 |
| BUSY | 11 | GP8 |
| SDCS | 12 | GP9 |
| MEMCS | 17 | GP13 |

No `ENA` wire is used with the EYESPI connector.

### Button Wiring

| Pico Pin | GPIO | Button | Function |
|----------|------|--------|----------|
| 14 | GP10 | SW1 | Previous page / Up |
| 15 | GP11 | SW2 | Next page / Down |
| 16 | GP12 | SW3 | Select / Menu |

All buttons: GPIO → button → GND. Active low with internal pull-up (no external resistors needed).

### Power Wiring

The [Pimoroni Pico LiPo SHIM (PIM557)](https://shop.pimoroni.com/products/pico-lipo-shim) solders directly to the back of the Pico:

| SHIM pad | Pico pad |
|----------|----------|
| VBUS | VBUS (pin 40) |
| VSYS | VSYS (pin 39) |
| GND | GND (pin 38) |
| 3V3_EN | 3V3_EN (pin 37) |

Battery connects via JST-PH 2-pin on the SHIM. Battery level read via Pico ADC3 (VSYS/3).

## SPI Bus Sharing

```mermaid
flowchart TD
    SPI[SPI0 Bus<br/>SCK · MOSI · MISO]
    
    SPI --> Display["🖥️ eInk Display<br/>CS: GP5 (TCS)"]
    SPI --> SRAM["32KB SRAM<br/>CS: GP13 (MEMCS)"]
    SPI --> SD["💾 microSD Card<br/>CS: GP9 (SDCS)"]
    
    Note1["Only one CS asserted at a time"]
    Note1 -.-> SPI
    
    style SPI fill:#e1e1e1,stroke:#333,color:#000
    style Display fill:#fff9c4,stroke:#333
    style SRAM fill:#c8e6c9,stroke:#333
    style SD fill:#c8e6c9,stroke:#333
```

## Power Flow

```mermaid
flowchart LR
    USB["USB 5V"] --> SHIM["LiPo SHIM<br/>MCP73831"]
    BAT["LiPo Battery<br/>3.7V"] --> SHIM
    SHIM --> Pico["Pico VSYS<br/>(~5V USB or ~3.7V bat)"]
    Pico --> Reg["Pico 3V3 Regulator"]
    Reg --> EYESPI["EYESPI VIN<br/>3.3V"]
    EYESPI --> Display["ThinkInk Display"]
    
    style USB fill:#ffccbc,stroke:#333
    style BAT fill:#c8e6c9,stroke:#333
    style SHIM fill:#fff9c4,stroke:#333
    style Display fill:#e1e1e1,stroke:#333,color:#000
```
