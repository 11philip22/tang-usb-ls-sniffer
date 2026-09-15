# Tang Nano 9K USB Low-Speed Sniffer HAT

Receive-only inline keystroke decoding for 1.5 Mb/s USB; passive data tap with FPGA-gated target VBUS

| | |
|---|---|
| **Status** | Revision A hardware baseline with gated target power; FPGA decoder and UART output not implemented yet |
| **Target** | Tang Nano 9K / GW1NR-LV9, 3.3 V header GPIO |
| **Scope** | Direct host-to-low-speed-device segment only |
| **Intended output** | Decoded characters over UART; USB/HID decoding and character conversion run on the FPGA |
| **Design priority** | Data-line transparency first; deterministic enumeration capture second |

The intended output is decoded keystrokes, meaning **decoded characters**. The FPGA interprets the keyboard traffic and converts it to characters before sending it over UART. The computer receiving the UART stream does not need to decode USB/HID traffic or translate key identities into characters. UART representation is not yet decided.

The [schematic](../hardware/board/tang_nano_hat.kicad_sch) and [PCB](../hardware/board/tang_nano_hat.kicad_pcb) are the source of truth for the BOM; this plan does not maintain a separate component list.

> **NON-NEGOTIABLE ELECTRICAL RULE**  
> J3 port A D+ connects directly to port B D+ and port A D− directly to port B D−. The HAT adds no pull-up, pull-down, 45 Ω termination, common-mode choke, switch, repeater, or FPGA output to either data wire. The FPGA can only observe buffered copies.

# 1. Recommended architecture

**Block diagram — the heavy lines are uninterrupted copper paths**

```text
HOST PC                 PASS-THROUGH HAT                       LS DEVICE
USB connection -> J3 USB-A port A                 port B -> target

VBUS        =====+==== U3 AP2151DWG-7 power switch ============= VBUS
                  |
                  +--> divider --> FPGA VBUS_SENSE
                       FPGA VBUS_EN --> U3 EN
D+          ==================================================== D+
                              |
                              +-- 100 ohm --> U1B RX --> FPGA DP_RX (logical DP)
D-          ==================================================== D-
                              |
                              +-- 100 ohm --> U1A RX --> FPGA DM_RX (logical DM)
GND         ==================================================== GND

Tang Nano 3V3 --> U1 and fitted R11 U3 fault pull-up
Tang Nano GND --> common ground
```

The baseline front end is one SN74LVC2G17 dual non-inverting Schmitt buffer powered from 3.3 V. Its two inputs are high impedance, 5.5 V tolerant, support powered-off Ioff operation, and specify about 4 pF input capacitance per channel. At low speed, this is a smaller and safer design than attaching a bidirectional USB transceiver.

Estimated added capacitive load is about 4.7 pF per data wire before PCB parasitics: 4 pF receiver input plus one 0.7 pF ESD channel. Set an assembled-board target below 8 pF per wire. The 100 Ω tap resistors isolate input capacitance and ESD kickback; they are not in the host-to-device path.

U3 interrupts only target VBUS. D+/D− remain direct copper so the FPGA never drives or switches either data wire. Holding target VBUS off until the FPGA is ready to receive lets the sniffer observe the resulting low-speed attachment and enumeration from its first packet.

## Intended operating sequence

1. Attach the sniffer's `HOST` port to the USB host and power the Tang through its USB-C connector. R10 holds U3 disabled during FPGA configuration. Once configured, the FPGA drives `VBUS_EN=0` until it is ready to receive and interpret the keyboard traffic.
2. Attach the keyboard to the `KEYBOARD` port. Once host VBUS is present and the receive path is armed, the FPGA asserts `VBUS_EN`, allowing U3 to power the keyboard.
3. Observe the host's enumeration requests and the keyboard's replies. Read the configuration, HID, and **HID report descriptor** traffic into the FPGA; the report descriptor defines how to interpret the keyboard reports. The sniffer never requests descriptors itself.
4. Decode USB transactions and HID input reports on the FPGA, then convert keyboard input into characters using the keyboard layout selected for the implementation.
5. Send those decoded characters over UART.

The current hardware cannot detect an unpowered keyboard's insertion. VBUS enable is conditional on **host power and receiver readiness**, not device presence: if the FPGA becomes ready before step 2, target VBUS is already enabled when the keyboard is plugged in. Capture is armed in either order. Strictly waiting for physical insertion before enabling U3 would require a separate trigger or presence detector; that is not part of this baseline.

# 2. Connectors and data pass-through wiring

| **Node** | **Connector / pins** | **Required connection** |
|----|----|----|
| J3 port A | Stacked USB Type-A receptacle; 1 VBUS, 2 D−, 3 D+, 4 GND | Host side; label `HOST`. |
| J3 port B | Stacked USB Type-A receptacle; 5 VBUS, 6 D−, 7 D+, 8 GND | Low-speed target side; label `KEYBOARD`. |
| Data | J3.2 ↔ J3.6; J3.3 ↔ J3.7 | Direct copper. No series parts or test jumpers. |
| Power | J3.1 → U3 IN; U3 OUT → J3.5 | FPGA-gated 5 V path; never connect J3.1 directly to J3.5. |
| Ground | J3.4 ↔ J3.8 ↔ HAT/Tang GND | Solid ground plane; this design is not isolated. |
| Shields | J3.9–J3.12 shell tabs | Join together and provision C4 1 nF \|\| R8 1 MΩ to logic ground; use 0 Ω only if enclosure grounding requires it. |

The switched VBUS path makes the ports directional even though D+/D− remain electrically symmetric. Reversing the ports defeats source-side VBUS sensing and can expose U3 to unintended reverse-power conditions.

# 3. Receive-only data tap

**Baseline schematic-level connections — U1 = SN74LVC2G17DBVR**

```text
D- line ----+---- R6 100 ohm ---- U1.1 (1A)
            |                        U1.6 (1Y) -- R4 33 ohm -- DM_RX / FPGA 33 / TP1
            +---- U2 ESD to GND at the shared tap junction

D+ line ----+---- R7 100 ohm ---- U1.3 (2A)
                                     U1.4 (2Y) -- R5 33 ohm -- DP_RX / FPGA 30 / TP2

Tang 3V3 -------------------------- U1.5; C3 100 nF + C2 1 uF to GND
Tang GND -------------------------- U1.2
```

- Use the non-inverting 2G17, not the inverting 2G14, so FPGA state bits match the wires.
- Place R6/R7 at the D+/D− junction and U1 within 5 mm of them. Place R4/R5 at U1 outputs if the path to the Tang headers exceeds roughly 20 mm.
- Configure FPGA inputs as LVCMOS33 with internal pulls disabled. Never expose a bidirectional HDL port for DP_RX or DM_RX.
- TP1 is DM_RX on FPGA pin 33; TP2 is DP_RX on FPGA pin 30. Place both test pads only on U1 outputs. Do not place oscilloscope pads or headers on raw D+/D−; a passive probe can load the bus more than the sniffer.
## Alternative receivers (do not populate together)

| **Choice**                 | **When to use**                                                              | **Trade-off / hard constraint**                                                                                                                              |
| -------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| SN74LVC2G17 (baseline)     | First prototype and normal LS capture                                        | Known 4 pF typical input load; Schmitt thresholds are not a certified USB receiver mask.                                                                     |
| TLV3202 comparator         | A fixed, adjustable single-ended threshold is required                       | Use a shared ~1.4 V reference. Its data sheet does not specify input capacitance; characterize the assembled tap before claiming lower load.                 |
| TUSB1106 FS/LS transceiver | USB-qualified receiver behavior and VP/VM/RCV outputs justify more circuitry | Strap OE HIGH in hardware and SUSPND LOW; leave transmit inputs fixed. It still contains drivers, needs more supply/control wiring, and is not the baseline. |
# 4. VBUS switching, sensing, power, and protection

**Source-side sensing and FPGA-gated target power — U3 = AP2151DWG-7**

```text
J3.1 HOST_VBUS ----+------------------------------- U3.5 IN
                   |
                   +---- D1 6 V ESD/TVS ---- GND
                   |
                   +---- C5 100 nF --------- GND
                   |
                   +---- R1 100 kohm ----+---- R2 1 kohm ----> FPGA pin 34 VBUS_SENSE
                                         |
                                         +---- R3 150 kohm ---- GND
                                         |
                                         +---- C1 10 nF -------- GND

U3.1 OUT ---------------------------------------------- J3.5 KEYBOARD_VBUS
   |
   +---- C6 100 nF ---- GND

FPGA pin 40 VBUS_EN ---- R9 1 kohm ----+---- U3.4 EN
                                        |
                                      R10 3.9 kohm
                                        |
                                       GND

Tang 3V3 ---- R11 10 kohm (fitted) ---- U3.3 FLG ---- TP3 VBUS_FAULT_N
Tang GND ---------------------------- U3.2 GND
```

- Sense `HOST_VBUS` before U3. The 100 kΩ / 150 kΩ divider produces 3.0 V at 5.0 V and 3.15 V at 5.25 V. It draws about 20 µA. C1 gives a sub-millisecond filter; treat this as presence detection, not an analog voltage measurement.
- U3 is a 2.7–5.5 V, 500 mA continuous USB power-distribution switch with controlled rise time, reverse-current blocking, current/thermal protection, an active-low open-drain fault output, and internal output discharge. When U3 is disabled, the discharge path helps remove target power and produce a clean detach.
- R10 is a mandatory 3.9 kΩ, 1% pull-down. FPGA GPIOs are high impedance **with a weak pull-up during configuration**, not simply floating; R10 must overpower that pull-up to keep U3 disabled. See [Gowin UG290, Appendix A](https://cdn.gowinsemi.com.cn/UG290E.pdf). After configuration, use LVCMOS33 with at least 4 mA drive and internal pulls disabled; initialize `VBUS_EN` low before enabling the output, arm the receive path, verify `VBUS_SENSE`, and only then drive it high.
- Keep R9 at 1 kΩ, 1%. With both resistor tolerances included, the EN design checks are:
  - **Boot/off:** allow 150 µA FPGA pull-up current, 10 µA additional GPIO leakage, and 1 µA EN leakage. `161 µA × 3.939 kΩ = 0.634 V`, below U3's 0.8 V maximum guaranteed-low input level.
  - **Driven on:** at the minimum LVCMOS33 supply of 3.135 V, the FPGA guarantees at least `VCCIO - 0.4 V = 2.735 V` at the specified drive strength. Including worst-case R9/R10 division and 1 µA EN leakage gives at least 2.167 V at EN, above U3's 2.0 V minimum guaranteed-high level. Nominal enabled current through R9/R10 is about 0.67 mA.
  - Limits come from [GW1NR DS117, Tables 3-8, 3-11, and 3-12](https://cdn.gowinsemi.com.cn/DS117E.pdf) and the [AP2151D recommended operating conditions and electrical characteristics](https://www.diodes.com/datasheet/download/AP2151D.pdf).
- C5 and C6 are local 100 nF X7R bypass capacitors. Do not add bulk capacitance to intercepted or switched VBUS; the target already presents its own input capacitance.
- U3 is powered from `HOST_VBUS`. Power U1 and the rest of the HAT logic from the Tang Nano 3.3 V header. Power the Tang through its own USB-C connector and never backfeed it from either VBUS node.
- Fit R11 (10 kΩ) from Tang 3V3 to U3 FLG and provide TP3 (`VBUS_FAULT_N`) for fault monitoring. With Tang 3V3 present, R11 pulls this open-drain output high when no fault is asserted; U3 pulls it low for an overcurrent or overtemperature fault. This is not a power-good signal. TP3 is a test point only; no FPGA fault-input pin is assigned in the baseline.
- Fit one TPD2EUSB30A (U2) inline with the shared D+/D− tap junction. Fit D1 near J3 port A and keep its return short. U3 provides power-path protection but does not replace connector ESD protection.
# 5. Tang Nano 9K GPIO assignment

Use only 3.3 V Bank 2 header pins. The following adjacent, otherwise-unused header pins keep the HAT routing short. Confirm the installed board revision against the Sipeed schematic before fabrication.

| **Signal** | **FPGA package pin** | **Board label** | **Direction / constraint** |
|----|----|----|----|
| DP_RX (D+) | 30 | IOB13B | Input, LVCMOS33, PULL_MODE=NONE |
| DM_RX (D−) | 33 | IOB23A | Input, LVCMOS33, PULL_MODE=NONE |
| VBUS_SENSE | 34 | IOB23B | Input, LVCMOS33, PULL_MODE=NONE |
| VBUS_EN | 40 | IOB33B / RGB_HS | Output, LVCMOS33, drive ≥4 mA, PULL_MODE=NONE; initialize low before enabling output |
| CAP_TX | 28 | IOB11B | Output, LVCMOS33; decoded characters to an external 3.3 V USB-UART receiver |
| 3V3 / GND | Header power | 3V3 / GND | Front-end supply and common reference |

Connect CAP_TX and common GND to the external UART receiver for normal operation. This output is separate from the intercepted USB link.

> **Direct receiver mapping:** Physical USB D+ is sampled as `DP_RX` on FPGA pin 30 and physical USB D− is sampled as `DM_RX` on FPGA pin 33. No HDL input swap is required: logical `DP = DP_RX` and logical `DM = DM_RX`. This affects only the receive tap; the passive USB path remains D+↔D+ and D−↔D−.

> **VOLTAGE WARNING**  
> Tang Nano Bank 3 package pins 79–86 are 1.8 V. Do not connect 3.3 V receiver outputs to them. Pins 28, 30, 33–34, and 40 above are shown as 3.3 V Bank 2 on Sipeed’s schematic. FPGA pin 40 is also routed as the RGB LCD `HSYNC` signal; do not attach an RGB LCD while it is used as `VBUS_EN`.

# 6. Functional flow and hardware/software boundaries

Once host VBUS is present and the FPGA is ready to receive, the FPGA enables U3 to power the keyboard. It observes enumeration, obtains the HID report descriptor from the host/keyboard exchange, interprets the keyboard reports, converts the input to characters, and sends those characters over UART.

- **Hardware:** provides the buffered D+/D− inputs, source-side VBUS sensing, FPGA-controlled target power, and UART output connection listed in section 5. R10 holds U3 off during configuration; the FPGA takes over power control afterward.
- **USB host:** performs enumeration and requests the descriptors and keyboard reports. The sniffer observes this exchange; it does not act as a USB host or drive either data wire.
- **FPGA:** performs USB/HID decoding and character conversion. Safe input sampling and correct USB/HID interpretation are required, but the decoder architecture and implementation are not prescribed here.
- **UART receiver:** receives already-decoded characters. USB/HID decoding and key-to-character conversion are not delegated to the receiving computer.

## Decisions not yet made

- **UART representation:** readable text or binary, character encoding, baud rate, framing, and whether additional corruption detection is needed.
- **Keyboard compatibility:** which keyboards and report formats the first implementation will support and test, including the keyboard layout used for character conversion.
- **Failure/reconnect behavior:** what happens when descriptors are missed, a keyboard disconnects, or the UART receiver reconnects.

# 7. Decoded characters over UART

Output decoded keystrokes over UART; **keystrokes means decoded characters**, not key identities or press/release event records. UART representation remains to be decided as listed in section 6.

# 8. PCB and layout guidance

- Use a 4-layer board if practical: signal / solid ground / power / signal. A careful 2-layer board is acceptable at LS if the pair stays over a continuous ground pour.
- Place stacked connector J3 at the board edge and route directly between its two USB contact rows. Keep this pass-through path as short as the footprint allows and avoid vias.
- Route the pass-through as a 90 Ω differential pair using the actual stack-up. Match D+ and D− within 2 mm. Do not split the ground reference beneath it.
- Make each receiver branch a true short tap: junction → 100 Ω resistor → U1, with no connector, header, or probe pad on the raw branch. Target less than 5 mm from pair to U1 input.
- Place U2 inline with the shared tap junction and give it the shortest possible ground return with multiple stitching vias. Keep ESD discharge current away from U1 and the Tang headers.
- Keep fast FPGA/capture-output traces away from the USB pair. Do not route the on-board 27 MHz clock onto the HAT.
- Route J3.1 `HOST_VBUS` to U3 IN and U3 OUT to J3.5 `KEYBOARD_VBUS` with short, wide copper sized for 500 mA. Never pour across U3 in a way that shorts IN to OUT.
- Place U3, C5, C6, R9, and R10 together near the J3 VBUS pins. Place D1 and the source-side VBUS-sense branch on the J3.1 side of U3.
- Keep the `VBUS_EN` route and its FPGA pin-40 header connection away from D+/D−. Provide clearly directional `HOST` and `KEYBOARD` silkscreen.

# 9. Bring-up and test plan

1.  Unpowered inspection. Verify J3 orientation and `HOST`/`KEYBOARD` labels, D1 polarity, U1 pin 1, U3 pin 1, R11 fitted, TP3 accessible, and no solder bridge from D+/D− to power or ground.
2.  Continuity. With the Tang and USB cables removed, confirm J3 port A D+↔port B D+, D−↔D−, and GND↔GND. Confirm D+ and D− are not shorted and have no fitted pull resistors. With U3 disabled, J3.1 VBUS must not be shorted to J3.5 VBUS.
3.  Default-off power test. Leave the Tang unpowered, apply 5 V to J3.1, and confirm `HOST_VBUS` is present while `KEYBOARD_VBUS` remains discharged. Verify U3 EN stays below 0.8 V with the 3.9 kΩ R10 fitted. Repeat with the Tang absent.
4.  Gated-enumeration test. Power the Tang through USB-C with the low-speed target already connected. Scope U3 EN and `KEYBOARD_VBUS` throughout power-up and FPGA configuration: EN must stay below 0.8 V with no target-power pulse until capture is armed. Once the FPGA intentionally asserts `VBUS_EN`, EN must exceed 2.0 V, `KEYBOARD_VBUS` must ramp up, the target must assert its D− pull-up, and the host must begin reset/enumeration. Exercise both host/Tang power-up orders and FPGA reconfiguration.
5.  Receiver-state test. At LS idle, verify DP_RX=0 and DM_RX=1, matching logical DP=0 and DM=1 directly. Removing host VBUS must deassert VBUS_SENSE. Exercise reset and verify SE0 appears on both received bits.
6.  USB/HID decoding test. For a selected supported host/keyboard combination, verify that the FPGA observes enumeration, obtains the HID report descriptor, and correctly interprets keyboard reports. Check that malformed traffic does not become fabricated characters; the validation method depends on the eventual implementation.
7.  VBUS switching test. Deassert `VBUS_EN` and confirm `KEYBOARD_VBUS` discharges and the D− pull-up disappears. After the target has powered down, enable U3 and verify a fresh attachment. This checks the hardware's ability to remove and restore target power without prescribing a software retry policy or delay.
8.  Electrical stress test. Exercise repeated power-up sequences, full target-device current, and U3 fault behavior. Confirm target switching and faults do not backfeed or brown out the Tang.
9.  Loading A/B test. Compare device operation and D+/D− rise/fall behavior with the HAT inserted versus a short direct adapter. Use a low-capacitance active probe; a normal passive probe can invalidate this test.
10. End-to-end character test. Boot the sniffer, connect a selected supported keyboard, and type known text using the layout selected for the implementation. Verify that UART delivers the expected decoded characters without host-side USB/HID decoding or key-to-character conversion. Exercise both connection orders: keyboard present before VBUS enable and keyboard inserted after reception is already armed.

Tests for compatibility and failure/reconnect behavior will be specified once the open decisions in section 6 are made.

# 10. Acceptance criteria and limitations

## Acceptance criteria

- With J3 port A connected to the host and the Tang powered, the target remains unpowered until the FPGA capture path is ready, then enumerates and operates after `VBUS_EN` is asserted; no D+/D− drive is measurable from the HAT.
- For the selected supported host/keyboard combination, with the target connected before FPGA startup, the FPGA is ready before attachment and observes enumeration from its first packet, including the host's HID/report-descriptor requests.
- With `VBUS_EN=0`, U3 discharges `KEYBOARD_VBUS` sufficiently to produce a reliable detach before a subsequent enable. U3 faults must not backfeed or brown out the Tang.
- Assembled added load is targeted below 8 pF per data wire, and the tap causes no observable new link errors on the chosen device/cable set.
- Known-good LS USB/HID traffic is interpreted correctly. Malformed traffic must not become fabricated characters.
- The FPGA obtains the report layout from observed enumeration, decodes supported keyboard reports, and emits the expected characters for the selected keyboard layout over UART. USB/HID decoding and key-to-character conversion run on the FPGA, not the receiving computer.
- UART representation, supported keyboards/report formats, and failure/reconnect behavior remain undecided as listed in section 6; no specific protocol or recovery mechanism is an acceptance requirement yet.

## Limitations

- Low-speed only. Full-speed and high-speed traffic are not decoded.
- The intended output is decoded characters, but supported keyboards, report formats, and the layout used for character conversion have not yet been selected. Universal keyboard compatibility is not claimed.
- Passive descriptor discovery depends on the host requesting the needed information. The sniffer cannot issue a missing request or force boot protocol. Handling missed descriptors remains undecided. VBUS_SENSE detects host power, not an unpowered keyboard's presence.
- Not a USB compliance analyzer. The Schmitt thresholds are practical for clean LS buses but do not implement every USB receiver sensitivity and timing requirement.
- Not perfectly invisible. The estimated 4.7 pF nominal tap/protection load plus PCB parasitics can still disturb a marginal cable or device.
- No physical direction signal exists on a two-wire passive tap. Host/device direction can be inferred from protocol context for normal traffic, but malformed or colliding traffic can be ambiguous.
- No galvanic isolation. Host, device, HAT, and Tang grounds are common; do not use this design across hazardous ground differences.
- Direct-segment view only. When placed between a hub and a low-speed device it sees that downstream LS segment; it does not reveal traffic on the hub’s upstream full-speed/high-speed link.
- The data tap is passive, but the power path is not. The connectors are directional, and the target intentionally remains unpowered while the Tang is unpowered, absent, or configuring.
- The baseline is receive-only on USB. It cannot inject packets, electrically force a USB reset, supply VBUS independently, or emulate a host/device; it can only remove and restore host-supplied target VBUS—and no USB data transmit path should be added accidentally during FPGA changes.
# 11. Primary references

| **Primary design sources** | **Supporting sources** |
|----|----|
| [USB-IF — USB 2.0 specification](https://www.usb.org/document-library/usb-20-specification) | [TI — TUSB1106 product/data sheet](https://www.ti.com/product/TUSB1106) |
| [USB-IF — HID class specification 1.11](https://www.usb.org/sites/default/files/hid1_11.pdf) | [USB-IF — HID Usage Tables 1.5](https://www.usb.org/sites/default/files/hut1_5.pdf) |
| [TI — SN74LVC2G17 data sheet](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf) | [TI — TLV3202 data sheet](https://www.ti.com/lit/ds/symlink/tlv3202.pdf) |
| [TI — TPD2EUSB30A data sheet](https://www.ti.com/lit/ds/symlink/tpd2eusb30a.pdf) | [SHOU HAN — AF SS-JB17.6 data sheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1912111437_SHOU-HAN-AF-SS-JB17-6_C456021.pdf) |
| [Diodes Incorporated — AP2141D/AP2151D data sheet](https://www.diodes.com/datasheet/download/AP2151D.pdf) | [LCSC — AP2151DWG-7 / C264075](https://www.lcsc.com/product-detail/power-distribution-switches_diodes-incorporated-ap2151dwg-7_C264075.html) |
| [Sipeed — Tang Nano 9K hardware](https://wiki.sipeed.com/hardware/en/tang/Tang-Nano-9K/Nano-9K.html) | [onsemi — ESD5Z series data sheet](https://www.onsemi.com/pdf/datasheet/esd5z2.5t1-d.pdf) |
