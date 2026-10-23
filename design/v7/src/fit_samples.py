"""Small process/interface samples, not replacements for bought hardware."""
from __future__ import annotations

from pathlib import Path
from cadgen import build123d as bd
from shapes import box, cylinder, colored, outline, tail_key


def label_cut(text,x,y,z,size):
    font=Path(__file__).resolve().parents[1]/'assets/DejaVuSans-Bold.ttf'
    letters=bd.Text(text,font_size=size,font_path=font,align=(bd.Align.CENTER,bd.Align.CENTER))
    return bd.Pos(x,y,z)*bd.extrude(letters,amount=0.8)


def tail_socket_sample(p):
    # Horizontal keyway, like the production rear socket. Print with the
    # production socket's orientation/support strategy to compare the process.
    shape=box(62,24,20)
    for x,gap in ((-20,0.3),(0,0.4),(20,0.5)):
        shape-=bd.Pos(x,13,10)*bd.Rot(90,0,0)*bd.extrude(tail_key(p,gap),amount=21)
        shape-=label_cut(f'{gap:.1f}',x,-10,19.4,5)
    return colored(shape,'tail_clearance_samples_0.3_0.4_0.5_per_side','#4E595F')


def tail_key_sample(p):
    # Root lies flat with layers across its thickness, as on the real tail.
    length=p['tail_key_length'];r=p['tail_thickness']/2
    shape=bd.Pos(length,0,r)*bd.Rot(0,-90,0)*bd.extrude(tail_key(p),amount=length)
    shape+=box(4,20,p['tail_thickness'],length+2)
    return colored(shape,'tail_key_section_sample_with_pull_tab','#E9E6DC')


def phone_thickness_sample(p):
    throat=p['phone_thickness']+p['fit_gap'];wall=p['wall'];depth=18
    shape=box(throat+2*wall,wall,4,0,-(depth-wall)/2)
    for x in (-(throat+wall)/2,(throat+wall)/2):shape+=box(wall,depth,4,x)
    return colored(shape,'phone_thickness_gauge_8.8_mm_throat_NOT_width_height_check','#4E595F')


def screw_sample(p):
    shape=box(56,18,4)
    for x,diameter in ((-18,3.2),(-6,3.4),(6,3.6),(18,3.8)):
        shape-=cylinder(diameter/2,6,x,3,-1)
        shape-=label_cut(f'{diameter:.1f}',x,-4,3.4,3.5)
    return colored(shape,'M3_process_clearance_samples_3.2_3.4_3.6_3.8_mm','#4E595F')
