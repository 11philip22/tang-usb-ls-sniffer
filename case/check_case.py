"""Check exported meshes and reference STEP models, then render a preview.

Run without arguments after tang_nano_9k_case.py, with CadQuery 2.8 and trimesh.
Required reference models live in ../production and ../libraries, not the print ZIP.
"""
from pathlib import Path
import cadquery as cq
import trimesh
import tang_nano_9k_case as design

ROOT = Path(__file__).resolve().parent


def collision_volume(first, second):
    # Reject distant solid pairs before invoking expensive CAD booleans.
    a_parts = [(s, s.BoundingBox()) for s in first.Solids()]
    b_parts = [(s, s.BoundingBox()) for s in second.Solids()]
    volume = 0.0
    for a, ab in a_parts:
        for b, bb in b_parts:
            if all(getattr(ab, axis + 'max') > getattr(bb, axis + 'min') + 1e-6
                   and getattr(bb, axis + 'max') > getattr(ab, axis + 'min') + 1e-6
                   for axis in 'xyz'):
                volume += a.intersect(b).Volume()
    return volume


def check_meshes(base, lid):
    for name, part in [('base', base), ('lid', lid)]:
        mesh = trimesh.load_mesh(ROOT / f'tang_nano_9k_{name}.stl')
        assert mesh.is_watertight and mesh.is_winding_consistent, name
        assert mesh.body_count == 1 and mesh.volume > 0, name
        assert abs(mesh.volume - part.val().Volume()) < 1.0, name
        print(f'{name}: one watertight mesh, {len(mesh.faces)} triangles, '
              f'{mesh.volume:.1f} mm^3', flush=True)


def references(base, lid):
    production = ROOT.parent / 'production'
    tang_file = production / 'tang-solid-reference.step'
    hat_file = production / 'hat-fit-standard.step'
    connector_file = (ROOT.parent / 'libraries/C456021.3dshapes/'
                      'USB-A-TH_AF-SS-JB17.6.step')
    assert all(p.is_file() for p in [tang_file, hat_file, connector_file]), (
        'Reference STEP files missing; see case/README.md')
    # Manufacturer PCB is centred at about (-30, 9.64), top at z=0.
    # Exclude its two downward male-header models: actual mating headers
    # are not selected yet, and the generator checks their keepout instead.
    raw = cq.importers.importStep(str(tang_file)).solids().vals()
    tang = cq.Compound.makeCompound([
        s for s in raw if not (s.BoundingBox().xlen > 60 and
                               s.BoundingBox().zlen > 10)
    ]).translate((30, -9.64, design.PCB_TOP))
    assert len(tang.Solids()) == 241, 'Unexpected Tang reference revision'
    hat = cq.importers.importStep(str(hat_file)).val().translate((0, 0, design.HAT_Z))
    # EasyEDA STEP and WRL have different origins. Match the WRL used by
    # the PCB without altering its model settings or the library files.
    # STEP y=-8.95..8.65,z=-8.090841..12.15; WRL y=-12.812..4.788,
    # z=-4..16.240841 mm. Rotate with J3 (90 deg), then position at J3.
    j3 = (cq.importers.importStep(str(connector_file)).val()
          .translate((0, -3.862, 4.090841))
          .rotate((0, 0, 0), (0, 0, 1), 90)
          .translate((design.J3_X, 0, design.HAT_TOP)))
    assert abs(j3.BoundingBox().xmax - design.J3_FRONT_X) < .001
    for name, reference in [('Tang components', tang), ('HAT standard models', hat),
                             ('aligned J3', j3)]:
        for part in (base.val(), design.assembled_lid(lid).val()):
            volume = collision_volume(part, reference)
            assert volume < 1e-5, (name, 'enclosure collision', volume)
        print(f'{name}: no enclosure collision', flush=True)
    assert collision_volume(tang, hat) < 1e-5, 'Tang/HAT collision'
    assert collision_volume(tang, j3) < 1e-5, 'Tang/J3 collision'
    print('Tang and HAT component models do not intersect.', flush=True)
    return tang, hat, j3


def preview(base, lid, pcb, tang, hat, j3):
    import vtk

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1600, 1050)
    window.SetMultiSamples(8)
    blue, light_blue = (.16, .30, .43), (.31, .49, .61)
    green, metal = (.08, .35, .22), (.70, .72, .74)
    # The right-hand view removes half the base to reveal the stacked boards.
    cutaway = base.cut(design.box(0, -30, -1, 100, 60, 100)).val()
    scenes = [
        [(base.val(), blue), (design.assembled_lid(lid).val(), light_blue),
         (j3, metal)],
        [(cutaway, blue),
         (design.assembled_lid(lid).val().translate((0, 0, 17)), light_blue),
         (pcb.val(), green), (tang, metal), (hat, green), (j3, metal)],
    ]
    for index, objects in enumerate(scenes):
        renderer = vtk.vtkRenderer()
        renderer.SetViewport(index / 2, 0, (index + 1) / 2, 1)
        renderer.SetBackground(.95, .96, .97)
        window.AddRenderer(renderer)
        for shape, color in objects:
            if shape is None:
                continue
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(shape.toVtkPolyData(.02, .15, normals=True))
            mapper.ScalarVisibilityOff()
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetSpecular(.25)
            actor.GetProperty().SetSpecularPower(25)
            renderer.AddActor(actor)
        title = vtk.vtkTextActor()
        title.SetInput(['ASSEMBLED / USB-A END', 'CUTAWAY / LID LIFTED'][index])
        title.SetPosition(32, 975)
        title.GetTextProperty().SetFontSize(24)
        title.GetTextProperty().SetColor(.12, .2, .28)
        renderer.AddViewProp(title)
        note = vtk.vtkTextActor()
        recess = design.CASE_CENTER_X + design.OUTER_LENGTH / 2 - design.J3_FRONT_X
        note.SetInput([f'USB-A recess: {recess:.2f} mm\nUSB-C accessible at opposite end',
                       f'Provisional board gap: {design.STACK_GAP:.1f} mm'][index])
        note.SetPosition(32, 45)
        note.GetTextProperty().SetFontSize(19)
        note.GetTextProperty().SetColor(.2, .26, .32)
        renderer.AddViewProp(note)
        camera = renderer.GetActiveCamera()
        camera.SetPosition(115, -150, 105)
        camera.SetFocalPoint(0, 0, 20)
        camera.SetViewUp(0, 0, 1)
        camera.ParallelProjectionOn()
        renderer.ResetCamera()
        camera.Zoom(1.15)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(ROOT / 'tang_nano_9k_preview.png'))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    window.Finalize()
    print('Preview written.', flush=True)


if __name__ == '__main__':
    base, lid = design.build()
    pcb, interference = design.check(base, lid)
    check_meshes(base, lid)
    print(f'Only intended friction ribs overlap: {interference:.3f} mm^3', flush=True)
    tang, hat, j3 = references(base, lid)
    preview(base, lid, pcb, tang, hat, j3)
    print('All requested checks completed.', flush=True)
