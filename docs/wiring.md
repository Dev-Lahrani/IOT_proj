# Hardware Wiring Guide

## Circuit Diagram (Breadboard View)

```
                    Raspberry Pi GPIO
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    BREADBOARD                           │
│                                                         │
│  BUZZER                    LED                   VIBRATION
│  ┌──────┐              ┌──────┐                ┌──────┐ │
│  │      │              │  LED │                │      │ │
│  │  +   ├──► GPIO17   │  +   ├──► GPIO22      │  +   ├──► GPIO27
│  │      │              │      │                │      │ │
│  └──┬───┘              └──┬───┘                └──┬───┘ │
│     │                      │                      │     │
│     └──────────┬───────────┴──────────┬──────────┘     │
│                │                       │                │
│           ┌────┴────┐            ┌─────┴────┐          │
│           │ 330Ω   │            │  330Ω   │           │
│           │ resistor           │ resistor            │
│           └────┬────┘            └─────┬────┘          │
│                │                       │                │
│                └─────────┬─────────────┘                │
│                          │                              │
│                     ┌────┴────┐                          │
│                     │   GND   │ ◄── Pi Pin 6, 9, 14, 20, 25, 30, 34, 39
│                     └─────────┘                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Detailed Pin Connections

### Buzzer (GPIO 17)
```
Buzzer +  ───► GPIO 17 (Pin 11)
Buzzer -  ───► GND (Pin 6 or 9 or 14...)
```

### LED (GPIO 22)
```
LED Anode (+) ──► GPIO 22 (Pin 15)
LED Cathode (-) ──► 330Ω resistor ──► GND
```

### Vibration Motor (GPIO 27)
```
Motor positive ──► GPIO 27 (Pin 13)
Motor negative ──► GND
```

### GPS Module (Neo-6M)
```
GPS VCC ──► 5V (Pin 2 or 4)
GPS GND ──► GND (Pin 6)
GPS TX  ──► GPIO 15 (Pin 10) - Pi RX
GPS RX  ──► GPIO 14 (Pin 8) - Pi TX
```

## GPIO Pin Map (BCM)

```
    ┌────┬────┬────┬────┬────┬────┬────┬────┐
 3.3V│ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │
    ├────┼────┼────┼────┼────┼────┼────┼────┤
  GPIO2│ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │ 9  │10  │
    ├────┼────┼────┼────┼────┼────┼────┼────┤
  GPIO3│11  │12  │13  │14  │15  │16  │17  │18  │
    ├────┼────┼────┼────┼────┼────┼────┼────┤
    │19  │20  │21  │22  │23  │24  │25  │26  │
  GND├──┼───┼───┼───┼───┼───┼───┼───┼───┤GPIO10
    ├────┼────┼────┼────┼────┼────┼────┼────┤
  MOSI│27  │28  │29  │30  │31  │32  │33  │34  │
    ├────┼────┼────┼────┼────┼────┼────┼────┤
  MISO│35  │36  │37  │38  │39  │40  │41  │42  │
    └────┴────┴────┴────┴────┴────┴────┴────┘
     1   2   3   4   5   6   7   8   9  10
```

## Pin Connections Summary

| Component | GPIO (BCM) | Physical Pin | Wire Color (suggested) |
|-----------|------------|--------------|------------------------|
| Buzzer    | GPIO 17    | Pin 11       | Red                   |
| LED       | GPIO 22    | Pin 15       | Green                 |
| Vibration | GPIO 27    | Pin 13       | Yellow                |
| GPS TX    | GPIO 15    | Pin 10       | Orange                |
| GPS RX    | GPIO 14    | Pin 8        | White                 |
| 5V Power  | -          | Pin 2/4      | Red                   |
| GND       | -          | Pin 6,9,14...| Black                 |

## Step-by-Step Wiring

### 1. Prepare Breadboard
- Place Raspberry Pi on one side
- Insert components into breadboard rows

### 2. Wire LED
- Insert LED into breadboard
- Connect 330Ω resistor to LED cathode (shorter leg)
- Connect resistor to GND rail
- Connect LED anode to GPIO 22

### 3. Wire Buzzer
- Note: Active buzzer has internal oscillator (no resistor needed)
- Connect positive to GPIO 17
- Connect negative to GND rail

### 4. Wire Vibration Motor
- Connect positive to GPIO 27
- Connect negative to GND rail

### 5. Wire GPS Module
- Connect VCC to 5V (Pin 2 or 4)
- Connect GND to GND
- Connect TX to Pi RX (GPIO 15)
- Connect RX to Pi TX (GPIO 14)

## Safety Notes

1. **Always disconnect power before wiring**
2. **Use resistors with LED** to prevent burnout
3. **Don't exceed 5V** on any GPIO pin
4. **GPS needs 5V**, not 3.3V
5. **Buzzer/vibration can run on 3.3V or 5V** (5V = louder/stronger)
