"""Electronic components learning library: metadata, pinouts, ASCII symbols, and explanations."""
import os

COMPONENTS_DATA = [
    {
        "id": "ne555",
        "name": "NE555 Precision Timer IC",
        "display_name": "NE555",
        "subtitle": "Precision Timer IC",
        "category": "ICs",
        "package": "DIP-8 / SOIC-8",
        "pin_count": 8,
        "function": "Generates accurate timing pulses, square waves, and oscillations.",
        "simple_explanation": "Think of it as an electronic metronome or heartbeat. It turns on and off at an exact rhythm set by a resistor and capacitor.",
        "detailed_explanation": "The 555 timer contains 25 transistors, 2 diodes, and 15 resistors on a silicon chip. It operates in Astable (oscillator), Monostable (one-shot pulse), and Bistable (flip-flop) modes.",
        "symbol": """
        +-------------------+
        |       NE555       |
    VCC | 8               1 | GND
   TRIG | 2               7 | DISCH
    OUT | 3               6 | THRES
  RESET | 4               5 | CTRL
        +-------------------+""",
        "pinout": """Pin 1: GND (0V ground reference)
Pin 2: TRIGGER (Starts timing cycle when voltage drops below 1/3 VCC)
Pin 3: OUTPUT (High/Low output up to 200mA)
Pin 4: RESET (Active-low reset, tie to VCC if unused)
Pin 5: CONTROL (Allows fine-tuning timing voltage, tie 10nF cap to GND)
Pin 6: THRESHOLD (Ends timing cycle when voltage reaches 2/3 VCC)
Pin 7: DISCHARGE (Open collector to ground, discharges timing capacitor)
Pin 8: VCC (Supply voltage: +4.5V to +16V)""",
        "typical_uses": [
            "Blinking LED flashers and strobes",
            "PWM motor speed controllers",
            "Buzzer tone generators and siren circuits",
            "Relay time-delay circuits (e.g. 10-second delay)"
        ],
        "key_specs": "Supply Voltage: 4.5V - 16V | Max Output Current: 200mA | Max Frequency: ~500 kHz"
    },
    {
        "id": "lm358",
        "name": "LM358 Dual Operational Amplifier",
        "display_name": "LM358",
        "subtitle": "Dual Operational Amplifier",
        "category": "ICs",
        "package": "DIP-8 / SOIC-8",
        "pin_count": 8,
        "function": "Dual low-power operational amplifier designed to operate from a single power supply.",
        "simple_explanation": "A signal magnifier. It takes tiny analog electrical voltages (like from a microphone or light sensor) and boosts them up so a microcontroller can read them.",
        "detailed_explanation": "Contains two independent, high-gain, internally frequency-compensated operational amplifiers designed specifically to operate from a single power supply over a wide range of voltages.",
        "symbol": """
        +-------------------+
        |       LM358       |
   OUT1 | 1               8 | VCC (+)
   IN1- | 2               7 | OUT2
   IN1+ | 3               6 | IN2-
    GND | 4               5 | IN2+
        +-------------------+""",
        "pinout": """Pin 1: Output A
Pin 2: Inverting Input A (-)
Pin 3: Non-inverting Input A (+)
Pin 4: Ground (GND / 0V)
Pin 5: Non-inverting Input B (+)
Pin 6: Inverting Input B (-)
Pin 7: Output B
Pin 8: Positive Supply (+3V to +32V)""",
        "typical_uses": [
            "Sensor signal conditioning (amplifying thermocouple or piezos)",
            "Voltage comparators (e.g. darkness detector)",
            "Active audio filter circuits",
            "Current sense amplifiers"
        ],
        "key_specs": "Supply: 3V to 32V (Single supply) | Gain Bandwidth: 1.1 MHz | Low Supply Current: 500 uA"
    },
    {
        "id": "1n4007",
        "name": "1N4007 Silicon Rectifier Diode",
        "display_name": "1N4007",
        "subtitle": "Silicon Rectifier Diode",
        "category": "Diodes",
        "package": "DO-41",
        "pin_count": 2,
        "function": "Allows electric current to flow in one direction only, blocking reverse current.",
        "simple_explanation": "A one-way valve for electricity. Protects circuits from reverse battery connections and absorbs inductive flyback voltage from motor coils.",
        "detailed_explanation": "Standard recovery silicon rectifier diode rated for 1.0 Ampere forward current and 1000 Volts peak repetitive reverse voltage.",
        "symbol": """
        Anode (A)                 Cathode (K)
        --------|>|-------[Silver Band]-------
             (Current flows in arrow direction)""",
        "pinout": """Anode (Unmarked side): Positive incoming terminal
Cathode (Side with Silver Band): Current exits here; blocks reverse flow""",
        "typical_uses": [
            "Flyback / Freewheeling protection across relay coils & motors",
            "Reverse-polarity battery protection for electronics",
            "AC to DC bridge rectifiers",
            "Voltage clamping circuits"
        ],
        "key_specs": "Forward Current: 1.0A | Max Reverse Voltage: 1000V | Forward Drop: ~0.7V"
    },
    {
        "id": "1n4148",
        "name": "1N4148 High-Speed Switching Diode",
        "display_name": "1N4148",
        "subtitle": "High-Speed Switching Diode",
        "category": "Diodes",
        "package": "DO-35",
        "pin_count": 2,
        "function": "Ultra-fast silicon diode for switching, signal processing, and high-frequency clamping.",
        "simple_explanation": "A super-fast one-way gate for signals. Unlike bulky power diodes, it switches on and off in 4 nanoseconds, perfect for logic and communications.",
        "detailed_explanation": "Planar high-speed switching diode fabricated in planar technology, encapsulated in a hermetically sealed leaded glass SOD27 (DO-35) package.",
        "symbol": """
        Anode (A)                 Cathode (K)
        --------|>|-------[Black Band]-------""",
        "pinout": """Anode (Unmarked clear lead): Signal input
Cathode (Side with Black stripe): Blocks reverse voltage, conducts forward""",
        "typical_uses": [
            "High-speed digital signal gating and logic diode OR matrices",
            "Microcontroller GPIO input clamping & ESD transient protection",
            "General-purpose fast switching in RF and timing circuits",
            "Audio detector and distortion clipping circuits"
        ],
        "key_specs": "Reverse Voltage: 100V | Continuous Forward: 200mA | Reverse Recovery Time: 4 ns | Drop: 0.7V"
    },
    {
        "id": "atmega328p",
        "name": "ATmega328P 8-Bit Microcontroller",
        "display_name": "ATmega328P",
        "subtitle": "8-Bit AVR Microcontroller",
        "category": "Microcontrollers",
        "package": "DIP-28 / TQFP-32",
        "pin_count": 28,
        "function": "Programmable computer-on-a-chip, famously powering the Arduino Uno.",
        "simple_explanation": "The programmable brain of your circuit. You write code on your computer, upload it, and it controls motors, reads sensors, and communicates.",
        "detailed_explanation": "High-performance RISC AVR architecture executing powerful instructions in a single clock cycle, achieving throughputs approaching 1 MIPS per MHz.",
        "symbol": """
        +-------------------+
        |    ATmega328P     |
  RESET | 1              28 | PC5 (ADC5/SCL)
    RXD | 2              27 | PC4 (ADC4/SDA)
    TXD | 3              26 | PC3 (ADC3)
    VCC | 7              22 | GND
    GND | 8              20 | AVCC
  XTAL1 | 9              19 | PB5 (SCK/D13)
  XTAL2 | 10             18 | PB4 (MISO/D12)
        +-------------------+""",
        "pinout": """Pins 2-6, 11-13: Digital I/O (D0 to D7)
Pins 14-19: Digital I/O (D8 to D13) [D3, D5, D6, D9, D10, D11 support PWM]
Pins 23-28: Analog Inputs (A0 to A5 / ADC0 to ADC5)
Pins 7, 20: VCC & AVCC (+5V Power)
Pins 8, 22: GND (Ground)
Pins 9, 10: Crystal Oscillator (16 MHz typical)
Pin 1: Active-Low RESET""",
        "typical_uses": [
            "Arduino Uno and Nano boards",
            "Robotics, motor controllers, and sensor stations",
            "Industrial automation and custom embedded systems",
            "Home automation and IoT prototypes"
        ],
        "key_specs": "Flash: 32 KB | SRAM: 2 KB | EEPROM: 1 KB | Clock: 16-20 MHz | Voltage: 1.8V - 5.5V"
    },
    {
        "id": "esp32",
        "name": "ESP32 Wi-Fi & Bluetooth SoC",
        "display_name": "ESP32",
        "subtitle": "Wi-Fi & Bluetooth SoC",
        "category": "Microcontrollers",
        "package": "Module / QFN-48",
        "pin_count": 38,
        "function": "Dual-core 32-bit microcontroller with integrated 2.4GHz Wi-Fi and Bluetooth.",
        "simple_explanation": "A super-fast microcontroller with built-in Wi-Fi and Bluetooth. Perfect for connected Smart Home devices and IoT gadgets.",
        "detailed_explanation": "Features the Xtensa dual-core 32-bit LX6 microprocessor running up to 240 MHz, with ultra-low power coprocessor and rich peripheral set including capacitive touch, ADCs, DACs, and cryptographic hardware acceleration.",
        "symbol": """
        +-------------------+
        |   ESP-WROOM-32    |
    3V3 | 3.3V          GND | GND
     EN | Enable       GPIO23| MOSI
  GPIO36| VP           GPIO22| SCL
  GPIO39| VN           GPIO1| TX0
  GPIO34| Input Only   GPIO3| RX0
        +-------------------+""",
        "pinout": """3V3: Power input (+3.3V ONLY, not 5V tolerant!)
GND: System ground
EN: Chip enable / reset (pull high to run)
GPIO 0: Boot mode selection (pull low to flash firmware)
GPIO 21 (SDA), GPIO 22 (SCL): Default I2C bus
GPIO 18 (SCK), 19 (MISO), 23 (MOSI): Default SPI bus
ADC1 / ADC2: Up to 18 channels of 12-bit Analog-to-Digital conversion""",
        "typical_uses": [
            "Smart Home sensors and automated switches",
            "Weather stations uploading to the cloud",
            "Bluetooth beacons and wireless controllers",
            "Audio streaming and Web servers"
        ],
        "key_specs": "Dual-Core 240 MHz | Wi-Fi: 802.11 b/g/n | BLE 4.2 | 520 KB SRAM | 4MB Flash"
    },
    {
        "id": "arduino_uno",
        "name": "Arduino Uno R3 Development Board",
        "display_name": "Arduino Uno",
        "subtitle": "ATmega328P Dev Board",
        "category": "Microcontrollers",
        "package": "Development Board",
        "pin_count": 28,
        "function": "Open-source electronics prototyping platform based on the flexible ATmega328P.",
        "simple_explanation": "The beginner-friendly electronics standard. Plugs straight into your USB port and lets you control sensors, motors, screens, and relays with simple code.",
        "detailed_explanation": "Integrates an ATmega328P microcontroller with an ATmega16U2 programmed as a USB-to-serial converter, onboard 5V and 3.3V regulators, 16MHz ceramic resonator, and reset button.",
        "symbol": """
        +--------------------------+
        |     ARDUINO UNO R3       |
    USB | [===]      DIGITAL D0-D13| Pins
    PWR | ( O )       ANALOG  A0-A5| Pins
        |             POWER 5V/3V3 | Pins
        +--------------------------+""",
        "pinout": """Digital Pins 0-13: GPIO (D3, D5, D6, D9, D10, D11 support 8-bit PWM)
Analog In A0-A5: 10-bit analog-to-digital converter inputs
Power: 5V (regulated output), 3.3V (50mA output), GND, Vin (7-12V DC input)
Reset: Resets microcontroller when pulled LOW
ICSP Header: In-Circuit Serial Programming for firmware upload""",
        "typical_uses": [
            "Learning embedded electronics and robotics programming",
            "Rapid prototyping of sensor and actuator circuits",
            "STEM education and university engineering labs",
            "Home automation and interactive art installations"
        ],
        "key_specs": "Operating Voltage: 5V | Input Voltage: 7-12V | Clock: 16 MHz | Digital I/O: 14 | Flash: 32 KB"
    },
    {
        "id": "resistor_guide",
        "name": "10k Ohm Resistor & Color Code Guide",
        "display_name": "10k Ohm Resistor",
        "subtitle": "Passive Resistor & Color Guide",
        "category": "Passives",
        "package": "Axial / 0805 SMD",
        "pin_count": 2,
        "function": "Restricts the flow of electric current according to Ohm's Law (V = I * R).",
        "simple_explanation": "The most fundamental electronic component. It limits how much current flows so sensitive components like LEDs don't burn out.",
        "detailed_explanation": "Color code bands on through-hole resistors decode value in Ohms: Band 1 (1st digit), Band 2 (2nd digit), Band 3 (Multiplier / number of zeros), Band 4 (Tolerance: Gold +-5%, Silver +-10%).",
        "symbol": r"""
             Zigzag Symbol (US)               Box Symbol (IEC)
            ---/\/\/\/\/---                   ---[       ]---""",
        "pinout": """Resistors have NO polarity! Either lead can be connected to positive or negative.
Color Code Table:
Black: 0 | Brown: 1 | Red: 2 | Orange: 3 | Yellow: 4
Green: 5 | Blue: 6  | Violet: 7 | Gray: 8 | White: 9
Gold: x0.1 (+-5% tolerance) | Silver: x0.01 (+-10% tolerance)""",
        "typical_uses": [
            "Current limiting for LEDs (e.g. 220 Ohm - 330 Ohm for 5V)",
            "Pull-up and pull-down resistors for buttons (10k Ohm)",
            "Voltage divider circuits for analog sensing",
            "Timing circuits combined with capacitors (RC circuits)"
        ],
        "key_specs": "Common Power Ratings: 1/4W (0.25W), 1/2W, 1W | Standard Tolerances: +-1%, +-5%"
    },
    {
        "id": "capacitor_guide",
        "name": "Electrolytic & Ceramic Capacitors",
        "display_name": "Capacitors",
        "subtitle": "Smoothing & Filter Capacitors",
        "category": "Passives",
        "package": "Radial Can / Ceramic Disc",
        "pin_count": 2,
        "function": "Stores electrical energy electrostatically and filters out electrical noise.",
        "simple_explanation": "Like a miniature rechargeable battery that charges and discharges in microseconds. Smooths out bumps in power lines to keep voltages steady.",
        "detailed_explanation": "Passes AC signals while blocking DC. Ceramic capacitors (pF - nF) filter high-frequency noise. Electrolytic capacitors (uF - mF) smooth low-frequency power supply ripples.",
        "symbol": """
        Non-Polarized (Ceramic)          Polarized (Electrolytic)
              ---| |---                         ---|(---
                                                +   -""",
        "pinout": """Ceramic Capacitors: Non-polarized. Can be inserted in either direction.
Electrolytic Capacitors: POLARIZED!
- Shorter leg & stripe on can = NEGATIVE (-)
- Longer leg = POSITIVE (+)
WARNING: Connecting an electrolytic capacitor backwards can cause it to burst!""",
        "typical_uses": [
            "Decoupling capacitors (0.1 uF ceramic placed close to every IC chip)",
            "Power supply smoothing filter (100 uF to 1000 uF electrolytic)",
            "Audio signal coupling and DC blocking",
            "Oscillator timing circuits"
        ],
        "key_specs": "Capacitance: pF, nF, uF | Voltage Rating: 6.3V, 16V, 25V, 50V (Must exceed circuit voltage!)"
    },
    {
        "id": "lm7805",
        "name": "LM7805 +5V Voltage Regulator",
        "display_name": "7805",
        "subtitle": "+5V Linear Voltage Regulator",
        "category": "Power Regulators",
        "package": "TO-220 / TO-263",
        "pin_count": 3,
        "function": "Converts higher unregulated DC input voltage down to a stable, smooth +5V DC.",
        "simple_explanation": "A voltage step-down component. Feed it 7V to 25V (like a 9V battery or 12V adapter), and it gives you a rock-solid 5V for microcontrollers.",
        "detailed_explanation": "Linear voltage regulator using internal current limiting, thermal shutdown, and safe-area compensation, making it essentially indestructible under overloads.",
        "symbol": """
        +-------------------+
        |      LM7805       |
    IN  | 1               3 | OUT (+5V)
        |         2         |
        +---------+---------+
                  |
                 GND""",
        "pinout": """Pin 1 (Left): INPUT (7V to 25V DC)
Pin 2 (Center / Metal Tab): GROUND (0V)
Pin 3 (Right): OUTPUT (+5V regulated DC, up to 1.5A with heat sink)""",
        "typical_uses": [
            "Powering 5V microcontrollers from 9V/12V power supplies",
            "USB power adapter circuits",
            "Audio equipment power filtering",
            "Instrumentation and bench power supplies"
        ],
        "key_specs": "Output: +5.0V +-4% | Max Current: 1.5A (with heatsink) | Dropout Voltage: ~2.0V"
    },
    {
        "id": "2n2222",
        "name": "2N2222 NPN Bipolar Junction Transistor",
        "display_name": "2N2222",
        "subtitle": "NPN BJT Transistor",
        "category": "Transistors",
        "package": "TO-92 / TO-18",
        "pin_count": 3,
        "function": "An electronic switch and amplifier. A small current controls a much larger current.",
        "simple_explanation": "An electronic relay with no moving parts. A tiny signal from a microcontroller pin turns on a powerful fan, LED strip, or relay.",
        "detailed_explanation": "NPN silicon planar epitaxial transistor designed for high-speed, medium-power switching and general-purpose amplifier applications.",
        "symbol": r"""
             Collector (C)
                 |
               --+--
             /   |   \
    Base (B) ----| -> \ (Arrow points OUT for NPN)
                 |
                 |
             Emitter (E)""",
        "pinout": """Facing the flat side of TO-92 (pins pointing down):
Pin 1 (Left): Emitter (Connect to Ground)
Pin 2 (Center): Base (Connect to signal via ~1k Ohm resistor)
Pin 3 (Right): Collector (Connect to load negative terminal)""",
        "typical_uses": [
            "Switching relays, buzzers, and DC motors from Arduino pins",
            "LED strip driving circuits",
            "Audio pre-amplifiers and signal boosters",
            "Logic inverter gates"
        ],
        "key_specs": "Vce: 40V | Continuous Collector Current: 800mA | hFE (Gain): 100 - 300 | Transition Freq: 250 MHz"
    },
    {
        "id": "hcsr04",
        "name": "HC-SR04 Ultrasonic Distance Sensor",
        "display_name": "HC-SR04",
        "subtitle": "Ultrasonic Distance Sensor",
        "category": "Sensors",
        "package": "Module",
        "pin_count": 4,
        "function": "Measures distance from 2cm to 400cm by bouncing high-frequency sound waves.",
        "simple_explanation": "Uses echolocation just like a bat. Emits a 40kHz sound burst and measures how long it takes for the echo to bounce back.",
        "detailed_explanation": "Send a 10us HIGH pulse to the TRIG pin. The module transmits eight 40kHz sonic bursts and pulls the ECHO pin HIGH for the exact duration until the bounce is received. Distance = (Echo Time * Speed of Sound) / 2.",
        "symbol": """
        +-------------------+
        |      HC-SR04      |
        | [TX]         [RX] |
        +--|---|---|---|----+
          VCC TRIG ECHO GND""",
        "pinout": """VCC: +5V DC power
TRIG: Trigger input (Send 10 microsecond TTL pulse to start)
ECHO: Echo pulse output (Measures sound flight time in microseconds)
GND: 0V Ground""",
        "typical_uses": [
            "Obstacle-avoiding robots",
            "Liquid level and tank volume measurement",
            "Parking assistant sensors and alarms",
            "Interactive presence detectors"
        ],
        "key_specs": "Range: 2cm - 400cm | Accuracy: 3mm | Operating Voltage: 5V DC | Working Angle: 15 deg"
    },
    {
        "id": "dht11",
        "name": "DHT11 Temperature & Humidity Sensor",
        "display_name": "DHT11",
        "subtitle": "Temp & Humidity Sensor",
        "category": "Sensors",
        "package": "Module",
        "pin_count": 4,
        "function": "Calibrated digital temperature and relative humidity sensor with single-wire interface.",
        "simple_explanation": "A dual-purpose weather sensor in a blue plastic shell. Reads both the room temperature and air humidity using a single microcontroller pin.",
        "detailed_explanation": "Uses a capacitive humidity sensor and a thermistor to measure surrounding air, outputting a digital signal on the data pin (no analog input pins needed).",
        "symbol": """
        +-------------------+
        |       DHT11       |
        |    [|||||||||]    |
        +--|---|---|---|----+
           1   2   3   4
          VDD DATA NC GND""",
        "pinout": """Pin 1: VDD (Power supply: 3V to 5.5V DC)
Pin 2: DATA (Single-bus bidirectional data; connect with 4.7k-10k pullup to VDD)
Pin 3: NC (Not connected / null)
Pin 4: GND (Ground reference 0V)""",
        "typical_uses": [
            "Smart home climate control and thermostats",
            "Indoor weather stations and data loggers",
            "Greenhouse humidity and temperature monitoring",
            "Dehumidifier control systems"
        ],
        "key_specs": "Humidity Range: 20-90% RH (5% accuracy) | Temp Range: 0-50 C (2 C accuracy) | Sampling: 1 Hz"
    }
]

PILL_CATEGORIES = [
    "All", "Diodes", "ICs", "Microcontrollers", "Passives", "Power Regulators", "Sensors", "Transistors"
]

def normalize_category(cat):
    if not cat:
        return "All"
    c = cat.strip()
    if c in ("Integrated Circuits", "ICs"):
        return "ICs"
    if c in ("Power & Regulators", "Power Regulators"):
        return "Power Regulators"
    return c

def get_all_components():
    return COMPONENTS_DATA

def get_categories():
    return list(PILL_CATEGORIES)

def get_package_types():
    return [
        "All Packages",
        "DIP (Through-Hole)",
        "TO-220 / TO-92",
        "DO-41 / DO-35",
        "Module / Dev Board",
        "Passive / SMD"
    ]

def get_component_image_path(comp_id, img_type="photo"):
    exts = [".png", ".jpg", ".jpeg"]
    candidates = [
        os.path.join("data", "images", "components", comp_id, f"{img_type}{ext}")
        for ext in exts
    ] + [
        os.path.join("public", "components", comp_id, f"{img_type}{ext}")
        for ext in exts
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None

def filter_components(category="All", search_query="", package="All Packages", pin_filter="All Pins", sort_by="Name (A-Z)"):
    results = []
    norm_cat = normalize_category(category)
    q = (search_query or "").strip().lower()

    for c in COMPONENTS_DATA:
        # Category filter
        c_norm = normalize_category(c["category"])
        if norm_cat != "All" and c_norm != norm_cat:
            continue

        # Package filter
        pkg = c.get("package", "").lower()
        if package == "DIP (Through-Hole)" and "dip" not in pkg:
            continue
        elif package == "TO-220 / TO-92" and not ("to-220" in pkg or "to-92" in pkg):
            continue
        elif package == "DO-41 / DO-35" and not ("do-41" in pkg or "do-35" in pkg):
            continue
        elif package == "Module / Dev Board" and not ("module" in pkg or "board" in pkg):
            continue
        elif package == "Passive / SMD" and not ("axial" in pkg or "smd" in pkg or "radial" in pkg or "ceramic" in pkg):
            continue

        # Pin filter
        pins = c.get("pin_count", 0)
        if pin_filter == "2-3 Pins" and not (2 <= pins <= 3):
            continue
        elif pin_filter == "4-8 Pins" and not (4 <= pins <= 8):
            continue
        elif pin_filter == "14+ Pins" and pins < 14:
            continue

        # Search query filter
        if q:
            searchable = f"{c['id']} {c['name']} {c.get('display_name','')} {c['category']} {c.get('subtitle','')} {c.get('package','')} {c['function']} {c['simple_explanation']} {c.get('key_specs', '')} {' '.join(c.get('typical_uses', []))}".lower()
            if q not in searchable:
                continue

        results.append(c)

    # Sorting
    if sort_by == "Name (Z-A)":
        results.sort(key=lambda x: x.get("display_name", x["name"]), reverse=True)
    elif sort_by == "Category":
        results.sort(key=lambda x: (x["category"], x.get("display_name", x["name"])))
    else: # Name (A-Z)
        results.sort(key=lambda x: x.get("display_name", x["name"]))

    return results

def find_component_match(text):
    if not text:
        return None
    t = str(text).lower()
    for c in COMPONENTS_DATA:
        cid = c["id"].lower()
        if cid in t:
            return c
        for token in [c["id"], c.get("display_name", "").lower(), c["name"].split()[0].lower()]:
            if len(token) >= 3 and token in t:
                return c
        if "resistor" in t and "resistor" in cid:
            return c
        if "capacitor" in t and "capacitor" in cid:
            return c
        if ("ultrasonic" in t or "sonar" in t or "distance" in t) and "hcsr04" in cid:
            return c
        if ("555" in t or "timer" in t) and "ne555" in cid:
            return c
        if ("arduino" in t or "uno" in t) and ("arduino_uno" in cid or "atmega" in cid):
            return c
        if ("atmega" in t or "328" in t) and "atmega" in cid:
            return c
        if ("esp32" in t or "wifi" in t or "bluetooth" in t) and "esp32" in cid:
            return c
        if ("7805" in t or "regulator" in t) and "lm7805" in cid:
            return c
        if ("2n2222" in t or "npn" in t or "transistor" in t) and "2n2222" in cid:
            return c
        if ("4148" in t) and "1n4148" in cid:
            return c
        if ("4007" in t or "rectifier" in t or "diode" in t) and "1n4007" in cid:
            return c
        if ("dht11" in t or "humidity" in t) and "dht11" in cid:
            return c
        if ("op amp" in t or "operational amplifier" in t or "358" in t) and "lm358" in cid:
            return c
    return None
