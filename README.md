# Tang Nano 9K USB Low-Speed Sniffer HAT

A receive-only USB sniffer HAT for the Tang Nano 9K, designed to observe **1.5 Mb/s low-speed USB** traffic, including compatible keyboards. The USB data lines pass directly between host and device; buffered copies go to the FPGA. An FPGA-controlled power switch delays device attachment until capture is ready.

> [!IMPORTANT]
> This repository currently contains the hardware design, enclosure, and capture specification. `hdl/` is a placeholder: the FPGA receiver, live HID decoder, and host capture software are not implemented. There is no working sniffer bitstream or configured HDL build yet.

![CAD preview of the assembled enclosure and a cutaway showing the Tang Nano 9K and HAT](hardware/case/tang_nano_9k_preview.png)

[Design plan](docs/plan.md) · [KiCad project](hardware/board/tang_nano_hat.kicad_pro) · [Case guide](hardware/case/README.md)

## Repository layout

| Path | Contents |
| --- | --- |
| [docs/plan.md](docs/plan.md) | Electrical design, pin mapping, planned decoder and record format, BOM recommendations, and bring-up checks. |
| [hardware/board/](hardware/board/) | KiCad schematic and PCB, project-local symbols, footprints, and 3D models. |
| [hardware/case/](hardware/case/) | Parametric CadQuery enclosure, printable STLs, STEP models, fit checker, and preview. |
| [hdl/](hdl/) | Reserved for FPGA logic, constraints, and tests; currently empty apart from `.gitkeep`. |

## Hardware

Open [hardware/board/tang_nano_hat.kicad_pro](hardware/board/tang_nano_hat.kicad_pro) in **KiCad 10** with its standard symbol, footprint, and 3D model libraries installed. Keep the adjacent `libraries/`, `fp-lib-table`, and `sym-lib-table` with the project so its custom parts resolve correctly.

The design uses:

- **SN74LVC2G17DBVR:** a dual non-inverting Schmitt buffer for the receive-only D+/D− tap.
- **TPD2EUSB30A:** low-capacitance protection at the data-line tap.
- **AP2151DWG-7:** target VBUS switching with output discharge, controlled by the FPGA.
- **Stacked dual USB-A connector:** separate `HOST` and `KEYBOARD` ports.

The ports are directional because VBUS is switched. Power the Tang through its own USB-C connector; the target receives host-supplied VBUS through the HAT. Do not backfeed the Tang from either VBUS node.

### FPGA connections

These are **FPGA package pin numbers**, not header positions.

| Signal | Pin | Direction at FPGA | Purpose |
| --- | --- | --- | --- |
| `DP_RX` | 30 | Input | Buffered USB D+. |
| `DM_RX` | 33 | Input | Buffered USB D−. |
| `VBUS_SENSE` | 34 | Input | Host-side VBUS presence, through the divider. |
| `VBUS_EN` | 40 | Output | Active-high target power enable; start low. |

Use LVCMOS33 and disable internal pulls on the three inputs. `DP_RX` and `DM_RX` must remain input-only. Pin 40 is also used by the Tang's RGB LCD interface, so do not attach an RGB LCD while using it for `VBUS_EN`. Optional capture-output pins are listed in the [design plan](docs/plan.md).

The planned startup sequence holds target power off, initializes capture, checks `VBUS_SENSE`, and then asserts `VBUS_EN`. This lets the receiver observe attachment and the host's enumeration requests. HID descriptors are returned in response to host requests, not sent spontaneously at power-up.

## Case

The enclosure is a two-piece, screwless design with accessible USB-A ports and Tang USB-C. Download the [base STL](hardware/case/tang_nano_9k_base.stl) and [lid STL](hardware/case/tang_nano_9k_lid.stl) for slicing, or use the [assembled STEP](hardware/case/tang_nano_9k_case.step) for CAD work.

> [!WARNING]
> The case assumes a **12 mm gap from the Tang's top PCB surface to the HAT's underside**. Measure the fully seated mating headers before printing. Physical fit and closed-case temperatures have not been tested; the image above is a CAD preview.

To regenerate the models, install Python 3.12 and run these PowerShell commands from the **repository root**:

```powershell
py -3.12 -m venv hardware/case/.venv
& .\hardware\case\.venv\Scripts\python.exe -m pip install -r hardware/case/requirements.txt
& .\hardware\case\.venv\Scripts\python.exe .\hardware\case\tang_nano_9k_case.py
```

Then check the geometry, meshes, and component fit and regenerate the preview:

```powershell
& .\hardware\case\.venv\Scripts\python.exe .\hardware\case\check_case.py
```

The checker takes **no command-line arguments** and uses the included Tang, HAT, and connector reference models. After PCB changes, refresh `hardware/case/hat-fit-standard.step` using the KiCad export command in the [case guide](hardware/case/README.md#generate-models-and-preview) before checking fit. Outputs are written beside the scripts; the checker does not regenerate STLs or export the PCB automatically.

## FPGA HDL

The planned receiver uses the Tang's **27 MHz clock**, giving 18 samples per nominal low-speed USB bit. The [design plan](docs/plan.md) covers synchronization, clock recovery, NRZI decoding, bit unstuffing, packet/CRC checks, bus events, and buffered capture records. Live keystroke decoding additionally needs enumeration tracking and HID report-descriptor parsing.

The intended open-source toolchain is **Yosys → nextpnr-himbaechel → Apicula `gowin_pack`**, with `openFPGALoader` for programming. The Tang Nano 9K uses device `GW1NR-LV9QN88PC6/I5` and family `GW1N-9C`. See [Apicula's Gowin build instructions](https://github.com/YosysHQ/apicula#getting-started).

[Apio](https://fpgawars.github.io/apio/docs/supported-boards/) supports this board as `sipeed-tang-nano-9k` and can manage the build workflow. It has not been configured in this repository: RTL, pin constraints, testbenches, and an `apio.ini` still need to be added before an HDL build can run.

## Scope and bring-up

- **Low-speed devices only.** A keyboard is not necessarily low-speed; full-speed and high-speed traffic are outside this design's scope.
- **Observe, do not transmit.** D+/D− remain direct copper; no FPGA output, pull resistor, or switch belongs in the pass-through data path. Only target VBUS is gated.
- **Shared ground, no isolation.** Host, device, HAT, and Tang grounds are connected.
- **Not a compliance analyzer.** The tap adds capacitance and must be checked on the actual device and cable combination.

Before connecting a target, work through the [bring-up and acceptance checks](docs/plan.md): inspect polarity and port orientation, verify unpowered continuity, confirm default-off target power, and compare captures against an independent trace once firmware exists. Leave the optional VBUS bypass `JP1` open for normal gated operation.
