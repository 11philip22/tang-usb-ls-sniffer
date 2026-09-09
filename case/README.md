# Tang Nano 9K + USB LS HAT case

Two-piece, screwless enclosure for the Tang Nano 9K and the [USB low-speed sniffer HAT](../docs/plan.md). The stacked USB-A ports face one end; the Tang's USB-C connector remains accessible at the other.

![Assembled enclosure and cutaway showing the HAT stack](tang_nano_9k_preview.png)

> [!IMPORTANT]
> The design assumes a **12 mm gap from the Tang's top PCB surface to the HAT's underside**. Measure your fully seated mating headers before printing. This is not total stack height. Physical fit and closed-case temperatures have not been tested.

## Files

| File | Purpose |
| --- | --- |
| [tang_nano_9k_base.stl](tang_nano_9k_base.stl) | Printable base, bottom down. |
| [tang_nano_9k_lid.stl](tang_nano_9k_lid.stl) | Printable lid, outside face down. |
| [tang_nano_9k_case.step](tang_nano_9k_case.step) | Editable base and lid in assembled position. |
| [tang_nano_9k_case.py](tang_nano_9k_case.py) | Parametric CadQuery source; exports the STLs and STEP. |
| [check_case.py](check_case.py) | Checks geometry, meshes and component fit, then generates the preview. |
| [tang_nano_9k_preview.png](tang_nano_9k_preview.png) | Assembled and cutaway views. |

## Generate models and preview

Run these PowerShell commands from the **repository root**, not from inside `case`.

Generate the printable models after changing dimensions:

```powershell
& .\case\.venv\Scripts\python.exe .\case\tang_nano_9k_case.py
```

Run all checks and generate the preview:

```powershell
& .\case\.venv\Scripts\python.exe .\case\check_case.py
```

`check_case.py` takes **no command-line options**. It always checks the exported meshes and reference models, then replaces `case/tang_nano_9k_preview.png`. Allow a few minutes. It does not regenerate the STL files or export the PCB automatically.

For a new environment, use Python 3.12 with CadQuery 2.8.0 and trimesh. If you use `uv`, create the environment once:

```powershell
uv venv --python 3.12 case/.venv
uv pip install --python case/.venv/Scripts/python.exe "cadquery==2.8.0" trimesh
```

### Required reference models

The generator can run without external board models. **The checker and preview require all three files below.** Paths are relative to the repository root.

| Path | Required contents |
| --- | --- |
| `production/hat-fit-standard.step` | Current HAT exported from KiCad with origin `135x63mm` and component filter `J1,J2,U3,C*,R*,D*`. |
| `production/tang-solid-reference.step` | The 243 solids from Sipeed's `Tang_Nano_9K_3672.step`, excluding its open/unbounded surfaces. |
| `libraries/C456021.3dshapes/USB-A-TH_AF-SS-JB17.6.step` | J3 connector model already included in the component library. |

`production/` is ignored by Git. The two generated board references are not included in the case ZIP, so a fresh clone or extracted ZIP alone is not sufficient to run `check_case.py`.

<details>
<summary>Prepare or refresh the reference files</summary>

Create `production` if needed. Export the HAT using KiCad's CLI (use the full path to `kicad-cli.exe` if it is not on `PATH`):

```powershell
New-Item -ItemType Directory -Force .\production | Out-Null
kicad-cli pcb export step --force --component-filter "J1,J2,U3,C*,R*,D*" --user-origin 135x63mm -o production/hat-fit-standard.step tang_nano_hat.kicad_pcb
```

`--force` replaces that generated STEP file. Re-export it after PCB changes. On restricted Windows setups, use the machine-wide KiCad installation and redirect `KICAD_CONFIG_HOME`, `TEMP` and `TMP` into workspace-local directories; KiCad may still need permission to initialize its Documents directory.

Download `Tang_Nano_9K_3672_step.rar` from [Sipeed's Tang Nano 9K 3D files](https://dl.sipeed.com/shareURL/TANG/Nano%209K/5_3D_file) and extract `Tang_Nano_9K_3672.step` into `production`. Prepare the solids-only reference:

```powershell
& .\case\.venv\Scripts\python.exe -c "import cadquery as cq; model = cq.importers.importStep('production/Tang_Nano_9K_3672.step'); cq.exporters.export(cq.Compound.makeCompound(model.solids().vals()), 'production/tang-solid-reference.step')"
```

The checker excludes the Tang reference's two downward male-header models and uses conservative header clearance volumes instead. Choose actual complementary male/female headers; the illustrated models do not specify a mating pair.

</details>

## Fit and adjustments

Current model dimensions are **78 × 32.4 × 40.7 mm**, with 2 mm walls, floor and lid, and 4 mm clearance below the Tang PCB. Both PCBs are nominally 70 × 26 × 1.6 mm.

J3 is at KiCad **X=162.3, Y=63 mm, rotation 90°**, giving approximately **0.39 mm recess** behind the case face. The shared USB-A opening is 20 × 18.5 mm; the USB-C opening is 14 × 8 mm with bevelled corners.

Adjust the constants at the top of `tang_nano_9k_case.py`:

- `STACK_GAP`: measured Tang-top to HAT-underside distance. Values below 10 mm require a new component-clearance assessment and are rejected.
- `LID_GAP` / `RIB_PROJECTION`: loosen or tighten the lid's friction fit.
- `PEG_DIAMETER`: fit of the locating pegs in the Tang's mounting holes.
- `USB_A_WIDTH`, `USB_WIDTH` and `USB_HEIGHT`: connector/cable clearance.
- `J3_X`: connector X position relative to the PCB centre: **KiCad X minus 135 mm**. The reference model and clearance checks share this value.

After changing dimensions, regenerate both parts and rerun the checker. **Do not scale the STLs** to change the stack gap. Re-export the HAT reference after moving components; changes to connector rotation, Y position or board outline require corresponding source updates.

J3's raw STEP and the WRL used by the PCB have different origins. The checker aligns the STEP by `(0, -3.862, +4.090841)` mm before rotation and placement. Do not substitute the raw STEP blindly in a board export. U1/U2 clearance is checked using a conservative component envelope.

## Print and assemble

- Print in millimetres at **100% scale**, using the orientations already stored in the STLs.
- Suggested starting settings: PETG, 0.4 mm nozzle, 0.20 mm layers, 3 perimeters, 4 top/bottom layers and 20% infill.
- Inspect the slicer preview: USB-C has a 10 mm bridge, plus small retaining lips and lid ribs. The USB-A notch opens to the seam, so it needs no additional roof bridge. Support needs depend on the printer.
- Test the empty lid first. Lightly sand tight ribs rather than forcing the lid. Add a brim if long edges lift.

1. Disconnect power and cables, clean the prints and fully mate the boards with the correct pin mapping. HAT components face up; USB-A faces the Tang's HDMI end.
2. Tilt the stack slightly and slide the Tang's USB-C end under the retaining lips. Lower the HDMI end onto the pegs through its 2.2 mm mounting holes.
3. Fit the lid. Its stops end 0.30 mm above clear HAT edge areas; they must not preload or bend the PCB. The mating headers retain the stack.
4. Check full cable insertion before powering up. Label the USB-A ports `HOST` and `KEYBOARD` according to the PCB mapping.

Use the side thumb recess to remove the lid. HDMI, GPIO, buttons and the card slot are not externally accessible. The enclosure is not waterproof, has no dedicated ventilation, and does not allow for a heatsink or extra modules.

## Validation and troubleshooting

Checks cover single valid CAD solids, watertight and consistently wound STL meshes, mesh/CAD volume agreement, PCB and component clearance, and an unobstructed USB-A cable path. Only the small lid friction ribs intentionally overlap the base. These checks do not replace measuring hardware or a physical test print.

- **Missing reference files:** prepare all three files listed above. The checker does not download or generate them automatically.
- **Mesh mismatch or collision assertion:** regenerate the STLs after source changes, refresh the HAT reference after PCB edits, and inspect the reported interference. Do not bypass the assertions.
- **Windows crash at shutdown:** the local CadQuery installation has completed exports/checks and then crashed during Python cleanup, even for a unit cube. Similar behaviour is tracked in [CadQuery issue #1911](https://github.com/CadQuery/cadquery/issues/1911). Confirm `Preview written.` and `All requested checks completed.` appear and the PNG is refreshed. An early crash or failed assertion is not a completed check; the shutdown issue still causes a nonzero process exit.
