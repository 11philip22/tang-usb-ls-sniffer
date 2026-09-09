# Tang Nano 9K USB Low-Speed Sniffer HAT

Receive-only inline capture for 1.5 Mb/s USB; passive data tap with FPGA-gated target VBUS

| | |
|---|---|
| **Status** | Revision A — buildable baseline with gated target power |
| **Target** | Tang Nano 9K / GW1NR-LV9, 3.3 V header GPIO |
| **Scope** | Direct host-to-low-speed-device segment only |
| **Design priority** | Data-line transparency first; deterministic enumeration capture second |

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

Tang Nano 3V3 --> U1 and optional U3 fault pull-up
Tang Nano GND --> common ground
```

The baseline front end is one SN74LVC2G17 dual non-inverting Schmitt buffer powered from 3.3 V. Its two inputs are high impedance, 5.5 V tolerant, support powered-off Ioff operation, and specify about 4 pF input capacitance per channel. At low speed, this is a smaller and safer design than attaching a bidirectional USB transceiver.

Estimated added capacitive load is about 4.7 pF per data wire before PCB parasitics: 4 pF receiver input plus one 0.7 pF ESD channel. Set an assembled-board target below 8 pF per wire. The 100 Ω tap resistors isolate input capacitance and ESD kickback; they are not in the host-to-device path.

U3 interrupts only target VBUS. D+/D− remain direct copper so the FPGA never drives or switches either data wire. Holding target VBUS off until the FPGA receiver and capture buffers are ready forces a new low-speed attachment and lets the sniffer observe enumeration from its first packet.

# 2. Connectors and data pass-through wiring

| **Node** | **Connector / pins** | **Required connection** |
|----|----|----|
| J3 port A | Stacked USB Type-A receptacle; 1 VBUS, 2 D−, 3 D+, 4 GND | Host side; label `HOST`. |
| J3 port B | Stacked USB Type-A receptacle; 5 VBUS, 6 D−, 7 D+, 8 GND | Low-speed target side; label `KEYBOARD`. |
| Data | J3.2 ↔ J3.6; J3.3 ↔ J3.7 | Direct copper. No series parts or test jumpers. |
| Power | J3.1 → U3 IN; U3 OUT → J3.5 | FPGA-gated 5 V path; never connect J3.1 directly to J3.5 except through optional bypass JP1. |
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
                                      R10 100 kohm
                                        |
                                       GND

Tang 3V3 ---- R11 10 kohm (DNP) ---- U3.3 FLG ---- TP3 VBUS_FAULT_N
Tang GND ---------------------------- U3.2 GND

JP1 (DNP) bridges U3 IN to OUT only for passive-link debugging.
```

- Sense `HOST_VBUS` before U3. The 100 kΩ / 150 kΩ divider produces 3.0 V at 5.0 V and 3.15 V at 5.25 V. It draws about 20 µA. C1 gives a sub-millisecond filter; treat this as presence detection, not an analog voltage measurement.
- U3 is a 2.7–5.5 V, 500 mA continuous USB power-distribution switch with controlled rise time, reverse-current blocking, current/thermal protection, an active-low open-drain fault output, and internal output discharge. The discharge path makes an FPGA-requested power cycle look like a clean detach before re-enumeration.
- R10 is mandatory. It keeps U3 disabled while FPGA pin 40 is high impedance during configuration or while the Tang is absent. Configure `VBUS_EN` low first, arm the receive path and buffers, verify `VBUS_SENSE`, and only then drive `VBUS_EN` high.
- C5 and C6 are local 100 nF X7R bypass capacitors. Do not add bulk capacitance to intercepted or switched VBUS; the target already presents its own input capacitance.
- U3 is powered from `HOST_VBUS`. Power U1 and the rest of the HAT logic from the Tang Nano 3.3 V header. Power the Tang through its own USB-C connector and never backfeed it from either VBUS node.
- Leave R11 unpopulated unless `VBUS_FAULT_N` is used for test or assigned to a spare 3.3 V FPGA input. FLG may otherwise remain open.
- JP1 is normally open. Populating it disables VBUS gating and restores an always-powered target for debugging; it does not restore port interchangeability in normal documentation or silkscreen.
- Fit one TPD2EUSB30A (U2) inline with the shared D+/D− tap junction. Fit D1 near J3 port A and keep its return short. U3 provides power-path protection but does not replace connector ESD protection.
# 5. Tang Nano 9K GPIO assignment

Use only 3.3 V Bank 2 header pins. The following adjacent, otherwise-unused header pins keep the HAT routing short. Confirm the installed board revision against the Sipeed schematic before fabrication.

| **Signal** | **FPGA package pin** | **Board label** | **Direction / constraint** |
|----|----|----|----|
| DP_RX (D+) | 30 | IOB13B | Input, LVCMOS33, PULL_MODE=NONE |
| DM_RX (D−) | 33 | IOB23A | Input, LVCMOS33, PULL_MODE=NONE |
| VBUS_SENSE | 34 | IOB23B | Input, LVCMOS33, PULL_MODE=NONE |
| VBUS_EN | 40 | IOB33B / RGB_HS | Output, LVCMOS33; initialize low before enabling output |
| CAP_TX (optional) | 28 | IOB11B | Output, LVCMOS33; external USB-UART |
| CAP_CTS (optional) | 29 | IOB13A | Input, LVCMOS33; omit for buffered captures |
| 3V3 / GND | Header power | 3V3 / GND | Front-end supply and common reference |

> **Direct receiver mapping:** Physical USB D+ is sampled as `DP_RX` on FPGA pin 30 and physical USB D− is sampled as `DM_RX` on FPGA pin 33. No HDL input swap is required: logical `DP = DP_RX` and logical `DM = DM_RX`. This affects only the receive tap; the passive USB path remains D+↔D+ and D−↔D−.

> **VOLTAGE WARNING**  
> Tang Nano Bank 3 package pins 79–86 are 1.8 V. Do not connect 3.3 V receiver outputs to them. Pins 28–30, 33–34, and 40 above are shown as 3.3 V Bank 2 on Sipeed’s schematic. FPGA pin 40 is also routed as the RGB LCD `HSYNC` signal; do not attach an RGB LCD while it is used as `VBUS_EN`.

# 6. Clocking and FPGA receive path

Use the on-board 27 MHz oscillator directly. It provides 18 samples per nominal 1.5 Mb/s bit, so Revision A needs no PLL or external clock. Keep a small signed phase-correction parameter in the clock recovery loop so real device clock error and asymmetric front-end delays can be tuned during bring-up.

**FPGA receive/decode blocks**
```text
DP_RX / DM_RX
      |
2-FF synchronizers --> line-state classifier --> edge FIFO --> raw mode
      |
LS CDR (18x)
      |
NRZI decode --> bit unstuff
      |
PID/field parser + CRC checks
      |
records --> BRAM FIFO --> output
```

- **Synchronizer:** two flip-flops per receiver output. Sample the pair in the same clock domain; do not synchronize a derived J/K signal separately.
- **Line classifier:** use `DP = DP_RX` and `DM = DM_RX`, then encode {DP,DM} as SE0=00, J=01, K=10, SE1=11. For a low-speed device, idle is J (D− high).
- **Clock recovery:** detect sync transitions, center the first data sample, then advance 18 clocks per bit. Nudge phase by ±1 clock on credible edges; reject phase changes during SE0.
- **Decoder:** NRZI transition means 0; no transition means 1. Remove stuffed zeros after six consecutive ones and flag missing stuff bits.
- **Packet parser:** validate the PID nibble complement, decode token/data/handshake fields, check CRC5 or CRC16, and require a legal EOP. Preserve malformed packets with error flags.
- **Bus events:** recognize reset (extended SE0), suspend, resume, low-speed keep-alive EOP, VBUS edges, SE1, and capture overflow.
- **Buffers:** use on-chip BRAM first. Add the Tang’s PSRAM controller only if measured traces overflow BRAM; it is not needed to prove the electrical tap or decoder.
- **Power/enumeration sequencer:** hold `VBUS_EN=0` throughout FPGA configuration and receive-path reset. After `VBUS_SENSE=1`, synchronizers, decoder, and BRAM FIFO are ready, assert `VBUS_EN=1` and capture the resulting attach, reset, and enumeration. For a forced retry, set `VBUS_EN=0` for at least 20 ms, clear USB address/configuration/HID state, re-arm capture, and assert it again.
- **HID discovery:** a general live keystroke decoder must track control transactions from address 0 through `SET_ADDRESS`, configuration/interface selection, and fragmented HID/report-descriptor responses. The host requests these descriptors; the target does not transmit them spontaneously.
# 7. Capture record format

Emit a length-framed, little-endian binary stream. The FPGA should not generate pcapng directly; a host utility can translate records later. Every record begins with this 16-byte header.

| **Offset** | **Size** | **Field** | **Definition** |
|----|----|----|----|
| 0 | 2 | magic | 0x534C; wire bytes 4C 53 (‘LS’) |
| 2 | 1 | version | 1 |
| 3 | 1 | type | 1 packet; 2 bus event; 3 raw-edge block; 0x7F overflow |
| 4 | 4 | timestamp | 27 MHz absolute tick at record start; wraps after ~159 s |
| 8 | 2 | payload_len | Bytes following this header |
| 10 | 1 | flags | PID/CRC OK, stuff error, EOP error, truncated, direction inferred |
| 11 | 1 | pid_or_state | PID for packet; event/state code otherwise |
| 12 | 2 | sequence | Monotonic record counter; gaps expose loss |
| 14 | 2 | reserved | Write zero; retain for compatible extension |

Packet payload contains decoded bytes beginning with PID and ending before EOP; keep bytes even when CRC or framing fails. A raw-edge block payload is a sequence of 32-bit words: bits 31:2 are delta ticks since the prior edge and bits 1:0 are SE0/J/K/SE1. At worst case this raw format can reach about 6 MB/s, so buffer it locally and never assume a UART can sustain it.

A 3 Mbaud 8N1 UART is adequate for most decoded LS traces but not guaranteed for pathological traffic plus record overhead. The sequence counter and explicit OVERFLOW records are mandatory; silent loss makes a sniffer untrustworthy.
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

1.  Unpowered inspection. Verify J3 orientation and `HOST`/`KEYBOARD` labels, D1 polarity, U1 pin 1, U3 pin 1, JP1 open, and no solder bridge from D+/D− to power or ground.
2.  Continuity. With the Tang and USB cables removed, confirm J3 port A D+↔port B D+, D−↔D−, and GND↔GND. Confirm D+ and D− are not shorted and have no fitted pull resistors. With JP1 open and U3 disabled, J3.1 VBUS must not be shorted to J3.5 VBUS.
3.  Default-off power test. Leave the Tang unpowered, apply 5 V to J3.1, and confirm `HOST_VBUS` is present while `KEYBOARD_VBUS` remains discharged. Verify U3 EN is held low by R10; the unpowered FPGA-side node need not have a defined voltage.
4.  Gated-enumeration test. Power the Tang through USB-C with the low-speed target already connected. Confirm `VBUS_EN` stays low until capture is armed, then rises on FPGA pin 40. `KEYBOARD_VBUS` must ramp up, the target must assert its D− pull-up, and the host must begin reset/enumeration.
5.  Receiver-state test. At LS idle, verify DP_RX=0 and DM_RX=1, matching logical DP=0 and DM=1 directly. Removing host VBUS must deassert VBUS_SENSE. Exercise reset and verify SE0 appears on both received bits.
6.  Raw timing test. Capture sync and EOP edges at 27 MHz. Confirm a nominal bit spans about 18 clocks and EOP is two SE0 bit times followed by J. Tune only the digital phase correction; do not add analog loading to hide a decoder bug.
7.  Decode test. Capture the complete enumeration from address 0 and compare SETUP/GET_DESCRIPTOR bytes, address changes, HID/report descriptors, PIDs, and CRC results against an independent host software trace. Preserve and inspect any discrepancy as raw edges.
8.  FPGA power-cycle test. Deassert `VBUS_EN`, confirm `KEYBOARD_VBUS` and the D− pull-up disappear, wait at least 20 ms, then re-arm and assert `VBUS_EN`. Require a fresh, completely captured enumeration on every cycle.
9.  Stress test. Run repeated power cycles, reconnects, long idle/suspend/resume, maximum-length LS transfers, malformed/error cases if available, and full target-device current. Check U3 fault behavior and require explicit overflow records whenever buffering is exhausted.
10. Loading A/B test. Compare device operation and D+/D− rise/fall behavior with the HAT inserted versus a short direct adapter. Use a low-capacitance active probe; a normal passive probe can invalidate this test.
# 10. BOM-level recommendations

| **Ref.**   | **Recommended part / value**                | **Purpose / note**                                                         |
| ---------- | ------------------------------------------- | -------------------------------------------------------------------------- |
| U1         | TI SN74LVC2G17DBVR                          | Dual non-inverting Schmitt receiver; SOT-23-6; baseline tap.               |
| U2         | TI TPD2EUSB30ADRTR                          | One shared two-channel 0.7 pF USB ESD array, inline with the D+/D− tap.    |
| U3         | Diodes AP2151DWG-7; LCSC C264075            | 500 mA active-high USB power switch with output discharge; SOT-25-5; JLCPCB Extended. |
| D1         | onsemi ESD5Z6.0T1G; LCSC C82323              | 6 V VBUS ESD/TVS diode in SOD-523.                                         |
| J1/J2      | 2× generic 1×24, 2.54 mm mating headers     | Use male pins or female sockets to match the headers fitted to the Tang; verify stack height. |
| J3         | SHOU HAN AF SS-JB17.6                       | Stacked dual USB Type-A receptacle; port A is host and port B is keyboard. |
| JP1        | Solder jumper or 0 Ω footprint; DNP         | Optional U3 IN-to-OUT bypass for passive-link debugging only.              |
| R1         | 100 kΩ, 1%, 0603                            | VBUS-divider high side.                                                     |
| R2         | 1 kΩ, 1%, 0402/0603                         | VBUS-sense input isolation.                                                |
| R3         | 150 kΩ, 1%, 0603                            | VBUS-divider low side; output is 3.0 V at 5.0 V.                           |
| R4, R5     | 33 Ω, 1%, 0402/0603                         | Receiver-output damping for DM_RX / DP_RX.                                 |
| R6, R7     | 100 Ω, 1%, 0402/0603                        | D− / D+ tap-branch isolation.                                              |
| R8         | 1 MΩ, 0603/0805                             | Shell-to-logic-ground coupling.                                            |
| R9         | 1 kΩ, 1%, 0603; LCSC C21190                | Series isolation from FPGA pin 40 to U3 EN.                                |
| R10        | 100 kΩ, 1%, 0603; LCSC C25803              | U3 EN pull-down; guarantees target VBUS off during FPGA configuration.     |
| R11        | 10 kΩ, 1%, 0603; LCSC C25804; DNP          | Optional 3.3 V pull-up for U3 active-low FLG/TP3.                           |
| C1         | 10 nF, X7R, 6.3 V or higher                 | VBUS-sense filter.                                                         |
| C2         | 1 µF, X7R, 6.3 V or higher                  | U1 local bulk bypass.                                                      |
| C3         | 100 nF, X7R, 6.3 V or higher                | U1 local bypass.                                                           |
| C4         | 1 nF, 2 kV, X7R, 1206; LCSC C9196           | Shell-to-logic-ground coupling.                                            |
| C5, C6     | 100 nF, X7R, ≥10 V, 0603; LCSC C14663      | U3 input/output local bypass; do not substitute bulk capacitance.          |
# 11. Acceptance criteria and limitations

## Acceptance criteria

- With J3 port A connected to the host and the Tang powered, the target remains unpowered until the FPGA capture path is ready, then enumerates and operates after `VBUS_EN` is asserted; no D+/D− drive is measurable from the HAT.
- With the target connected before FPGA startup, every enable cycle captures attachment, reset, enumeration from address 0, and the host's HID/report-descriptor requests without a missing initial packet.
- With `VBUS_EN=0`, U3 discharges `KEYBOARD_VBUS` sufficiently to produce a reliable detach before a subsequent enable. U3 faults must not backfeed or brown out the Tang.
- Assembled added load is targeted below 8 pF per data wire, and the tap causes no observable new link errors on the chosen device/cable set.
- Known-good LS captures decode PIDs, bit stuffing, CRC5/CRC16, EOP, reset, and keep-alive correctly; malformed traffic is retained with flags.
- All capture loss is reported by sequence gaps and OVERFLOW records.

## Limitations

- Low-speed only. Full-speed and high-speed traffic are not decoded. A full-speed device may produce plausible edges but invalid records.
- Not a USB compliance analyzer. The Schmitt thresholds are practical for clean LS buses but do not implement every USB receiver sensitivity and timing requirement.
- Not perfectly invisible. The estimated 4.7 pF nominal tap/protection load plus PCB parasitics can still disturb a marginal cable or device.
- No physical direction signal exists on a two-wire passive tap. Host/device direction can be inferred from protocol context for normal traffic, but malformed or colliding traffic can be ambiguous.
- No galvanic isolation. Host, device, HAT, and Tang grounds are common; do not use this design across hazardous ground differences.
- Direct-segment view only. When placed between a hub and a low-speed device it sees that downstream LS segment; it does not reveal traffic on the hub’s upstream full-speed/high-speed link.
- The data tap is passive, but the power path is not. The connectors are directional, and the target intentionally remains unpowered while the Tang is unpowered, absent, or configuring unless JP1 is populated.
- The baseline is capture-only. It cannot inject packets, electrically force a USB reset, supply VBUS independently, or emulate a host/device; it can only remove and restore host-supplied target VBUS—and no data transmit path should be added accidentally during FPGA changes.
# 12. Primary references

| **Primary design sources** | **Supporting sources** |
|----|----|
| [USB-IF — USB 2.0 specification](https://www.usb.org/document-library/usb-20-specification) | [TI — TUSB1106 product/data sheet](https://www.ti.com/product/TUSB1106) |
| [TI — SN74LVC2G17 data sheet](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf) | [TI — TLV3202 data sheet](https://www.ti.com/lit/ds/symlink/tlv3202.pdf) |
| [TI — TPD2EUSB30A data sheet](https://www.ti.com/lit/ds/symlink/tpd2eusb30a.pdf) | [SHOU HAN — AF SS-JB17.6 data sheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1912111437_SHOU-HAN-AF-SS-JB17-6_C456021.pdf) |
| [Diodes Incorporated — AP2141D/AP2151D data sheet](https://www.diodes.com/datasheet/download/AP2151D.pdf) | [LCSC — AP2151DWG-7 / C264075](https://www.lcsc.com/product-detail/power-distribution-switches_diodes-incorporated-ap2151dwg-7_C264075.html) |
| [Sipeed — Tang Nano 9K hardware](https://wiki.sipeed.com/hardware/en/tang/Tang-Nano-9K/Nano-9K.html) | [onsemi — ESD5Z series data sheet](https://www.onsemi.com/pdf/datasheet/esd5z2.5t1-d.pdf) |
