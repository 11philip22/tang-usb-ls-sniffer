"""Tang Nano 9K + USB LS HAT enclosure. Units: mm. Requires cadquery 2.8.
Run: python tang_nano_9k_case.py
Exports two STLs in print orientation and a STEP assembly beside this file.
STACK_GAP is provisional: measure your mated headers before printing.
"""
from pathlib import Path
import cadquery as cq

# Fit adjustments; preserve the board dimensions and mounting-hole locations.
PCB_THICKNESS = 1.6
UNDER_BOARD = 4.0
HAT_THICKNESS = 1.6
STACK_GAP = 12.0                # Tang TOP surface to HAT BOTTOM; confirm physically.
HAT_HEADROOM = 17.5             # J3 model reaches 16.241 mm above the HAT.
LID_GAP = 0.20                  # Clearance on each side of the locating skirt.
RIB_PROJECTION = 0.30           # Local 0.10 mm interference; sand ribs if tight.
PEG_DIAMETER = 1.70             # Goes into the nominal 2.2 mm board holes.
USB_WIDTH = 14.0                # Includes clearance for the cable's plastic body.
USB_HEIGHT = 8.0
USB_CENTER_ABOVE_PCB = 1.80
USB_A_WIDTH = 20.0              # Shared opening for both cable overmoulds.
USB_A_BOTTOM = -1.0             # Relative to HAT top surface.
J3_X = 27.3                    # KiCad X=162.3 minus board-centre X=135.0.
J3_FRONT_X = J3_X + 12.812      # Aligned connector front, shared by fit checks.
WALL, FLOOR, LID_THICKNESS = 2.0, 2.0, 2.0
INNER_LENGTH, INNER_WIDTH = 74.0, 28.4
CASE_CENTER_X = 1.5             # Extra internal length beyond the HDMI end.
OUTER_LENGTH = INNER_LENGTH + 2 * WALL
OUTER_WIDTH = INNER_WIDTH + 2 * WALL
PCB_Z = FLOOR + UNDER_BOARD
PCB_TOP = PCB_Z + PCB_THICKNESS
HAT_Z = PCB_TOP + STACK_GAP
HAT_TOP = HAT_Z + HAT_THICKNESS
BASE_HEIGHT = HAT_TOP + HAT_HEADROOM
TOTAL_HEIGHT = BASE_HEIGHT + LID_THICKNESS
MOUNTS = [(32.35, -10.4), (32.35, 10.4)]


def box(x, y, z, dx, dy, dz):
    return cq.Workplane('XY').box(dx, dy, dz, centered=(True, True, False)).translate((x, y, z))


def rounded(length, width, height, radius, z=0):
    return (cq.Workplane('XY').box(length, width, height, centered=(True, True, False))
            .edges('|Z').fillet(radius).translate((CASE_CENTER_X, 0, z)))


def cylinder(x, y, z, diameter, height):
    return cq.Workplane('XY').circle(diameter / 2).extrude(height).translate((x, y, z))


def build():
    assert 0.1 <= LID_GAP <= 0.5
    assert 0 <= RIB_PROJECTION <= LID_GAP + 0.2
    assert 1.4 <= PEG_DIAMETER <= 1.9
    assert UNDER_BOARD >= 3.5 and STACK_GAP >= 10.0
    assert HAT_HEADROOM >= 17.0
    assert 18 <= USB_A_WIDTH <= 22
    assert 12 <= USB_WIDTH <= 16 and 7 <= USB_HEIGHT <= 10
    assert 1.2 <= PCB_THICKNESS <= 2.0

    base = rounded(OUTER_LENGTH, OUTER_WIDTH, BASE_HEIGHT, 3.2)
    base = base.cut(rounded(INNER_LENGTH, INNER_WIDTH, BASE_HEIGHT, 1.2, FLOOR))

    # Tang USB-C opening. Sloping upper corners shorten the bridge to 10 mm.
    z0 = PCB_TOP + USB_CENTER_ABOVE_PCB - USB_HEIGHT / 2
    z1 = z0 + USB_HEIGHT
    w = USB_WIDTH / 2
    opening = [(-w + 1, z0), (w - 1, z0), (w, z0 + 1), (w, z1 - 2),
               (w - 2, z1), (-w + 2, z1), (-w, z1 - 2), (-w, z0 + 1)]
    port = cq.Workplane('YZ', origin=(-39, 0, 0)).polyline(opening).close().extrude(7)
    base = base.cut(port)

    # HAT J3 is at (162.3, 63, 90 deg) on the 70 x 26 mm KiCad board.
    # Both ports face +X. Open to the seam: no new unsupported roof bridge,
    # and cable mouldings can reach the connector recessed behind the wall.
    usb_a_slot = box(CASE_CENTER_X + INNER_LENGTH / 2, 0,
                     HAT_TOP + USB_A_BOTTOM, 8, USB_A_WIDTH,
                     TOTAL_HEIGHT - HAT_TOP - USB_A_BOTTOM + 1)
    base = base.cut(usb_a_slot)

    for x, y in MOUNTS:
        base = base.union(cylinder(x, y, FLOOR - .05, 4.0, UNDER_BOARD + .05))
        peg = (cylinder(x, y, PCB_Z - .05, PEG_DIAMETER, PCB_THICKNESS - .15)
               .edges('>Z').chamfer(.15))
        base = base.union(peg)

    # The USB end slides below two shallow lips on unused PCB edge areas.
    # Their 0.55 mm overlap avoids the buttons and the pin-header bodies.
    for y in (-8.5, 8.5):
        base = base.union(box(-35.10, y, FLOOR - .05, 1.30, 2.0, UNDER_BOARD + .05))
        base = base.union(box(-35.10, y, PCB_TOP + .35, 1.30, 2.0, 1.2))

    # Lid is built outer face down, already in its printing orientation.
    lid = rounded(OUTER_LENGTH, OUTER_WIDTH, LID_THICKNESS, 3.2)
    skirt_l, skirt_w = INNER_LENGTH - 2 * LID_GAP, INNER_WIDTH - 2 * LID_GAP
    skirt = rounded(skirt_l, skirt_w, 3.5, 1.2, LID_THICKNESS - .05)
    skirt = skirt.cut(rounded(skirt_l - 2.4, skirt_w - 2.4, 4, .3, LID_THICKNESS - .10))
    lid = lid.union(skirt)

    # Small tapered ribs grip the base without screws or additional openings.
    for x in (-20, 20):
        for sign in (-1, 1):
            y = sign * skirt_w / 2
            rib = [(y - sign * .15, 2.1), (y, 2.1),
                   (y + sign * RIB_PROJECTION, 2.8),
                   (y + sign * RIB_PROJECTION, 3.6), (y, 4.6),
                   (y - sign * .15, 4.6)]
            lid = lid.union(cq.Workplane('YZ', origin=(x - 2, 0, 0))
                            .polyline(rib).close().extrude(4))

    # Stops retain the HAT without preload; narrow pegs locate its 2.2 mm holes.
    # Peg tips stop 0.2 mm above the HAT underside.
    # y is mirrored because the print-oriented lid is turned over for assembly.
    stop_tip = HAT_TOP + .30
    for x, y in MOUNTS:
        lid = lid.union(cylinder(x, -y, LID_THICKNESS - .05, 3.6,
                                 BASE_HEIGHT - stop_tip + .05))
        peg = (cylinder(x, -y, TOTAL_HEIGHT - stop_tip - .05, PEG_DIAMETER,
                        stop_tip - HAT_Z - .15).edges('>Z').chamfer(.15))
        lid = lid.union(peg)
    # Do not let the rear locating skirt hang into the USB-A cable opening.
    lid = lid.cut(box(CASE_CENTER_X + INNER_LENGTH / 2, 0,
                      LID_THICKNESS, 8, USB_A_WIDTH, 4))
    # A shallow external thumb recess helps remove the lid; it does not pierce it.
    lid = lid.cut(box(CASE_CENTER_X, -OUTER_WIDTH / 2, 1.2, 9, 1.0, .85))
    return base.clean(), lid.clean()


def assembled_lid(lid):
    return lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, TOTAL_HEIGHT))


def check(base, lid):
    # A runnable check travels with the editable design.
    for part in (base, lid):
        assert len(part.solids().vals()) == 1, 'Detached part'
        assert part.val().isValid(), 'Invalid CAD solid'
        assert part.val().Volume() > 0
    # Only the deliberately oversized friction ribs may overlap the base.
    interference = base.intersect(assembled_lid(lid)).val().Volume()
    assert 0 <= interference < 4.0, ('Unexpected lid collision', interference)
    pcb = cq.Workplane('XY').box(70, 26, PCB_THICKNESS, centered=(True, True, False))
    pcb = pcb.edges('|Z').fillet(2.5).translate((0, 0, PCB_Z))
    for x, y in MOUNTS:
        pcb = pcb.cut(cylinder(x, y, PCB_Z - 1, 2.2, PCB_THICKNESS + 2))
    assert base.intersect(pcb).val().Volume() < 1e-5
    assert assembled_lid(lid).intersect(pcb).val().Volume() < 1e-5
    hat = (cq.Workplane('XY').box(70, 26, HAT_THICKNESS,
                                 centered=(True, True, False))
           .edges('|Z').fillet(2.54).translate((0, 0, HAT_Z)))
    for x, y in MOUNTS:
        hat = hat.cut(cylinder(x, y, HAT_Z - 1, 2.2, HAT_THICKNESS + 2))
    # Conservative J3 body envelope from the aligned KiCad VRML model:
    # x=J3_X-4.788..J3_X+12.812, y=+-8.052, top=16.241 above HAT.
    # Pins below the PCB only span x=J3_X-4.288..J3_X+7.912;
    # add 0.1 mm end clearance, without inventing pins under the port mouth.
    keepouts = [hat, box(J3_X + 4.012, 0, HAT_TOP, 17.6, 16.104, 16.241),
                box(J3_X + 1.812, 0, HAT_TOP - 4.1, 12.4, 16.104, 4.1),
                box(-3.25, 0, HAT_TOP, 60.96, 26, 3.2)]
    for y in (-11.43, 11.43):
        keepouts.append(box(-3.25, y, PCB_Z - 3.0, 60.96, 2.54,
                            HAT_Z - PCB_Z + 3.0))
    for keepout in keepouts:
        for part in (base, assembled_lid(lid)):
            assert part.intersect(keepout).val().Volume() < 1e-5, 'Stack collision'
    # Ensure a continuous 20 mm cable path from the connector face outwards.
    cable_end = CASE_CENTER_X + OUTER_LENGTH / 2 + 1.0
    assert J3_FRONT_X < cable_end, 'Connector extends beyond cable-check region'
    cable_path = box((J3_FRONT_X + cable_end) / 2, 0, HAT_TOP + USB_A_BOTTOM,
                     cable_end - J3_FRONT_X, USB_A_WIDTH,
                     BASE_HEIGHT - HAT_TOP - USB_A_BOTTOM)
    for part in (base, assembled_lid(lid)):
        assert part.intersect(cable_path).val().Volume() < 1e-5, 'Blocked USB-A opening'
    return pcb, interference


if __name__ == '__main__':
    base, lid = build()
    _, interference = check(base, lid)
    output = Path(__file__).resolve().parent
    for name, part in [('base', base), ('lid', lid)]:
        cq.exporters.export(part, str(output / f'tang_nano_9k_{name}.stl'),
                            tolerance=.025, angularTolerance=.08)
    assembly = cq.Assembly(name='Tang_Nano_9K_USB_LS_HAT_case')
    assembly.add(base, name='base', color=cq.Color(.16, .30, .43))
    assembly.add(assembled_lid(lid), name='lid', color=cq.Color(.31, .49, .61))
    assembly.export(str(output / 'tang_nano_9k_case.step'))
    print(f'Checked: two valid solids; rib interference {interference:.3f} mm^3.')
    print(f'Assembled size: {OUTER_LENGTH:.1f} x {OUTER_WIDTH:.1f} x {TOTAL_HEIGHT:.1f} mm')
    print(f'PROVISIONAL header gap: {STACK_GAP:.1f} mm (Tang top to HAT underside).')
    print(f'USB-A recess: {CASE_CENTER_X + OUTER_LENGTH / 2 - J3_FRONT_X:.3f} mm.')
