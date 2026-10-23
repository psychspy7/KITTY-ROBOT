"""Single-part export checks and a flat build-plate datum."""
from cadgen import build123d as bd


def part(shape, p):
    solids=list(shape.solids())
    if len(solids)!=1 or not shape.is_valid or solids[0].volume<=0:
        raise ValueError(f'{shape.label}: expected one valid connected positive-volume solid, got {len(solids)}')
    bounds=shape.bounding_box()
    size=bounds.size
    if any(a>b for a,b in zip((size.X,size.Y,size.Z),(p['printer_x'],p['printer_y'],p['printer_z']))):
        raise ValueError(f'{shape.label}: exceeds assumed printer volume')
    return shape.moved(bd.Location((0,0,-bounds.min.Z)))
