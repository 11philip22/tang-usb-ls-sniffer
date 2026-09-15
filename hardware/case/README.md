# Tang Nano 9K + USB LS HAT case

![Case preview](tang_nano_9k_preview.png)

## Generate models and preview

PowerShell, from the **repository root**:

```powershell
# One-time setup (Python 3.12)
py -3.12 -m venv hardware/case/.venv
& .\hardware\case\.venv\Scripts\python.exe -m pip install -r hardware/case/requirements.txt

# Export the HAT reference from KiCad
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export step --force --component-filter "J1,J2,U3,C*,R*,D*" --user-origin 135x63mm -o hardware/case/3d/hat-fit-standard.step hardware/board/tang_nano_hat.kicad_pcb

# Generate the case STL and STEP files
& .\hardware\case\.venv\Scripts\python.exe .\hardware\case\tang_nano_9k_case.py

# Check fit and generate the preview
& .\hardware\case\.venv\Scripts\python.exe .\hardware\case\check_case.py
```

## Files

- [3d/tang_nano_9k_base.stl](3d/tang_nano_9k_base.stl) — printable base.
- [3d/tang_nano_9k_lid.stl](3d/tang_nano_9k_lid.stl) — printable lid.
- [3d/tang_nano_9k_case.step](3d/tang_nano_9k_case.step) — assembled case CAD model.
- [tang_nano_9k_preview.png](tang_nano_9k_preview.png) — generated preview.
- [tang_nano_9k_case.py](tang_nano_9k_case.py) — generates STL and STEP files.
- [check_case.py](check_case.py) — checks fit and generates the preview.
- [requirements.txt](requirements.txt) — Python dependencies.
- [3d/tang-solid-reference.step](3d/tang-solid-reference.step) — Tang reference for fit checks.
- [3d/hat-fit-standard.step](3d/hat-fit-standard.step) — HAT reference exported from KiCad.
