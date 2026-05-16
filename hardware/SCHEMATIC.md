# Altoid eInk Reader — Schematic

Raspberry Pi Pico wired to Adafruit 2.9″ Tri-Color eInk Breakout (SSD1680).

## System Block Diagram

```mermaid
flowchart LR
    subgraph Pico["🍓 Raspberry Pi Pico"]
        direction LR
        SPI0["SPI0<br/>GP2-4"]
        GP5["GP5"]
        GP6["GP6"]
        GP7["GP7"]
        GP8["GP8"]
        GP9["GP9"]
        GP10["GP10"]
        GP11["GP11"]
        GP12["GP12"]
        PWR["3V3<br/>GND"]
    end

    subgraph Display["🖥️ 2.9″ eInk Breakout<br/>(SSD1680, 128×296)"]
        SCK["SCK"]
        MOSI["MOSI"]
        MISO["MISO"]
        ECS["ECS"]
        DC["D/C"]
        RST["RST"]
        BUSY["BUSY"]
        SDCS["SDCS"]
        VIN["VIN"]
        GND_e["GND"]
        SD["microSD slot"]
    end

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
    GP5 --> ECS
    GP6 --> DC
    GP7 --> RST
    GP8 --> BUSY
    GP9 --> SDCS
    PWR --> VIN
    PWR --> GND_e
    GP10 --> UP
    GP11 --> DOWN
    GP12 --> SEL
    SHIM -- "solders under Pico" --> Pico
    BAT --> SHIM
    SDCS -.-> SD
```

## Pin Connections

| Pico Pin | GPIO | Signal | → | eInk Breakout |
|----------|------|--------|---|--------------|
| 4 | GP2 (SPI0 SCK) | SCK | → | SCK |
| 5 | GP3 (SPI0 TX) | MOSI | → | MOSI |
| 6 | GP4 (SPI0 RX) | MISO | → | MISO |
| 7 | GP5 | ECS | → | ECS |
| 9 | GP6 | D/C | → | D/C |
| 10 | GP7 | RST | → | RST |
| 11 | GP8 | BUSY | → | BUSY |
| 12 | GP9 | SDCS | → | SDCS |
| 36 | 3V3(OUT) | VIN | → | VIN |
| 38 | GND | GND | → | GND |

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
    
    SPI --> Display["🖥️ eInk Display<br/>CS: GP5 (ECS)"]
    SPI --> SD["💾 microSD Card<br/>CS: GP9 (SDCS)"]
    
    Note1["Only one CS asserted at a time"]
    Note1 -.-> SPI
    
    style SPI fill:#e1e1e1,stroke:#333,color:#000
    style Display fill:#fff9c4,stroke:#333
    style SD fill:#c8e6c9,stroke:#333
```

## Power Flow

```mermaid
flowchart LR
    USB["USB 5V"] --> SHIM["LiPo SHIM<br/>MCP73831"]
    BAT["LiPo Battery<br/>3.7V"] --> SHIM
    SHIM --> Pico["Pico VSYS<br/>(~5V USB or ~3.7V bat)"]
    Pico --> Reg["Pico 3V3 Regulator"]
    Reg --> Display["eInk Breakout VIN<br/>3.3V"]
    Reg --> SD["microSD Card<br/>3.3V"]
    
    style USB fill:#ffccbc,stroke:#333
    style BAT fill:#c8e6c9,stroke:#333
    style SHIM fill:#fff9c4,stroke:#333
    style Display fill:#e1e1e1,stroke:#333,color:#000
    style SD fill:#e1e1e1,stroke:#333,color:#000
```
