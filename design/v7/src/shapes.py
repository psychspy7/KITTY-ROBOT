"""V7 complete draft geometry. No hardware dimension here is fit-verified."""
from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd
from cadgen import srgb
from settings import datums, tail_placement


def box(w, d, h, x=0, y=0, z=0):
    return bd.Pos(x, y, z) * bd.Box(w, d, h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def cylinder(r, h, x=0, y=0, z=0):
    return bd.Pos(x, y, z) * bd.Cylinder(r, h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def octagon(w, d, corner):
    a, b = w/2, d/2
    return bd.Polygon((-a+corner,-b),(a-corner,-b),(a,-b+corner),(a,b-corner),
                      (a-corner,b),(-a+corner,b),(-a,b-corner),(-a,-b+corner))


def outline(w, d, h, corner, z=0):
    return bd.Pos(0,0,z) * bd.extrude(octagon(w,d,corner), amount=h)


def bore(shape, x, y, z, height, diameter):
    return shape - cylinder(diameter/2,height,x,y,z)


def colored(shape, name, color):
    shape.label = name
    shape.color = srgb(color)
    return shape


def wordmark(p, text, font_size, z, front):
    """Raised letters, embedded into a shell face, read from its outside."""
    slope=(p['body_depth']-p['top_depth'])/(2*(p['cover_top']-p['cover_shoulder']))
    if z <= p['cover_shoulder']:
        slope=0
    face_y=p['body_depth']/2-slope*max(0,z-p['cover_shoulder'])
    sign=-1 if front else 1
    plane=bd.Plane(origin=(0,sign*(face_y-p['letter_embed']),z),
                   x_dir=(1 if front else -1,0,0),z_dir=(0,sign,slope))
    font=Path(__file__).resolve().parents[1]/'assets/DejaVuSans-Bold.ttf'
    # Explicit tracking keeps adjacent cap bars, especially TT, separate.
    glyphs=[];cursor=0
    for char in text:
        glyph=bd.Text(char,font_size=font_size,font_path=font,
                      text_align=(bd.TextAlign.LEFT,bd.TextAlign.BOTTOM))
        bounds=glyph.bounding_box()
        glyphs.append(bd.Pos(cursor-bounds.min.X,0,0)*glyph)
        cursor+=bounds.size.X+p['letter_spacing']
    letters=bd.Compound(children=glyphs)
    bounds=letters.bounding_box()
    letters=bd.Pos(-(bounds.min.X+bounds.max.X)/2,-(bounds.min.Y+bounds.max.Y)/2,0)*letters
    return bd.extrude(plane*letters,amount=p['letter_relief']+p['letter_embed'],
                      dir=(0,sign,slope))


def base(p):
    z, t = p['base_z'], p['base_thickness']
    shape = outline(p['body_width'],p['body_depth'],t,p['corner'],z)
    patterns = [(x,y) for x in (-68,68) for y in (-65,65)]
    patterns += [(s*46,p['motor_y']+y) for s in (-1,1) for y in (-25,25)]
    patterns += [(s*44,p['battery_y']) for s in (-1,1)]
    patterns += [(x,p['electronics_y']+dy) for x in (-45,45) for dy in (-12,12)]
    patterns += [(x,p['caster_y']) for x in (-28,28)]
    patterns += [(x,-72) for x in (-25,25)]
    for x,y in patterns:
        shape = bore(shape,x,y,z-t,t*3,p['m3_clearance'])
    shape -= box(40,34,t*3,0,p['caster_y'],z-t)
    for x in (-25,25):
        shape -= box(3,18,t*3,x,p['battery_y'],z-t)
    return colored(shape,'base_chassis_DRAFT','#30383D')


def cover(p, front):
    w,d,c,t = p['body_width'],p['body_depth'],p['corner'],p['wall']
    low,shoulder,top = p['cover_bottom'],p['cover_shoulder'],p['cover_top']
    outer = bd.loft([bd.Pos(0,0,z)*octagon(x,y,c) for z,x,y in
                     ((low,w,d),(shoulder,w,d),(top,p['top_width'],p['top_depth']))], ruled=True)
    inner = bd.loft([bd.Pos(0,0,z)*octagon(x,y,c-t) for z,x,y in
                     ((low-t,w-2*t,d-2*t),(shoulder,w-2*t,d-2*t),
                      (top-t,p['top_width']-2*t,p['top_depth']-2*t))], ruled=True)
    shape = outer - inner
    shape -= box(40,20,2*t,0,0,top-2*t)
    for x in (-34,34):
        for y in (-23,23):
            shape = bore(shape,x,y,top-2*t,3*t,p['m3_clearance'])
    # Rounded service/sensor apertures keep the existing centres and access band.
    for x,y,z,width,height,radius in ((0,-d/2,43,64,40,5),
                                      (-12,d/2,44,34,20,3),
                                      (43,d/2,44,18,16,2)):
        aperture=bd.Plane.XZ*bd.RectangleRounded(width,height,radius)
        shape -= bd.Pos(x,y,z)*bd.extrude(aperture,amount=10,both=True)
    for y in (16,27,38,49):
        vent=bd.Plane.YZ*bd.SlotOverall(12,3,rotation=90)
        shape -= bd.Pos(0,y,77)*bd.extrude(vent,amount=w/2+6,both=True)
    sign = -1 if front else 1
    half = box(w+20,d,top+10,0,sign*(d/2+p['seam']/2),0)
    shape = shape & half
    for x in (-68,68):
        y=sign*65
        boss = cylinder(6,16,x,y,datums(p)['deck'])
        rib = box(18,5,10,x+(-7 if x<0 else 7),y,low)
        shape = shape + boss + (rib & outer)
        shape = bore(shape,x,y,datums(p)['deck']-1,20,p['m3_clearance'])
        nut = bd.Pos(x,y,datums(p)['deck']+13)*bd.extrude(bd.RegularPolygon(3.3,6),amount=4)
        shape -= nut
    if not front:
        shape += tail_socket(p)
        shape -= tail_socket_cavity(p)
        shape += wordmark(p,'KITTY',p['robot_font_size'],p['robot_wordmark_z'],False)
    else:
        brow=box(76,9,6,0,-d/2,61)
        shape += bd.chamfer(brow.edges(),length=1.5)
        # A broad folded collar follows the chest without thinning the shell.
        # The paired ruled sections give the positive relief a bevelled rim.
        slope=(d-p['top_depth'])/(2*(top-shoulder))
        panel=bd.Plane(origin=(0,-d/2+slope*(94-shoulder)+0.4,94),
                       x_dir=(1,0,0),z_dir=(0,-1,slope))
        emblem=bd.Polygon((-38,10),(-20,8),(0,-3),(20,8),(38,10),
                          (36,4),(20,2),(0,-11),(-20,2),(-36,4),align=None)
        relief=bd.loft([emblem,bd.Pos(0,0,2.2)*bd.scale(emblem,by=0.92)],ruled=True)
        shape += panel*relief
        shape += wordmark(p,'PROMETHEUS',p['team_font_size'],p['team_wordmark_z'],True)
    return colored(shape,'front_cover_DRAFT' if front else 'rear_cover_DRAFT','#E9E6DC')


def tail_key(p, clearance=0):
    """Asymmetric keyed cross-section in X/Z, local sketch Y becomes Z."""
    r=p['tail_thickness']/2;g=clearance
    # One clipped corner prevents the tail from being fitted upside down.
    profile=bd.Polygon((-r-g,-r-g),(r+g,-r-g),(r+g,r-3+g*(2**0.5-1)),
                       (r-3+g*(2**0.5-1),r+g),(-r-g,r+g),align=None)
    return profile


def tail_cross_bore(p):
    return (bd.Pos(-18,datums(p)['tail_y']-p['tail_bolt_inset'],p['tail_height'])
            * bd.Rot(0,90,0) * cylinder(p['m3_clearance']/2,36))


def tail_socket(p):
    """Rear-shell socket, blind inner end, cross screw and outside nut recess."""
    y=datums(p)['tail_y'];z=p['tail_height']
    depth=p['tail_socket_projection']+11
    shape=box(26,depth,24,0,y-depth/2,z-12)
    shape=bd.chamfer(shape.edges(),length=1.5)
    shape -= tail_cross_bore(p)
    # Nut enters from the right; screw enters from the left, above the wheels.
    nut=bd.extrude(bd.RegularPolygon(3.3,6),amount=3)
    shape -= bd.Pos(10,y-p['tail_bolt_inset'],z)*bd.Rot(0,90,0)*nut
    # The screw-entry side carries a rearward arrow below the cross bore.
    # It is a removal-direction cue, not a latch or a seated-fit indicator.
    arrow=bd.Polygon((-6,-1),(1,-1),(1,-2.5),(6,0),(1,2.5),(1,1),(-6,1),align=None)
    plane=bd.Plane(origin=(-12.6,y-10,z-8),x_dir=(0,1,0),z_dir=(1,0,0))
    shape += bd.extrude(plane*arrow,amount=1.2,dir=(-1,0,0))
    return shape


def tail_socket_cavity(p):
    # Cut after fusing the socket to the sloped shell so its inner wall cannot
    # partially fill the keyway when the tail moves closer to the body.
    return (bd.Pos(0,datums(p)['tail_y']+2,p['tail_height'])*bd.Rot(90,0,0)
            *bd.extrude(tail_key(p,p['tail_joint_gap']),amount=p['tail_key_length']+2))


def tail(p):
    """Flat-print curved tail with a keyed root, no servo or magnets assumed."""
    def points(*pairs):
        return [(x*p['tail_reach_scale'],y*p['tail_rise_scale']) for x,y in pairs]
    outer=bd.Spline(*points((0,-7),(26,0),(45,24),(48,49),(37,69),(17,75),(3,64)))
    tip=bd.ThreePointArc(*points((3,64),(-0.2,56.5),(7,53)))
    inner=bd.Spline(*points((7,53),(17,61),(29,57),(34,45),(31,28),(17,13),(0,7)))
    root=bd.Line(*points((0,7),(0,-7)))
    body=bd.extrude(bd.Face(bd.Wire([outer,tip,inner,root])),amount=p['tail_thickness'],dir=(0,0,1))
    # Bevel only the two exposed perimeter rims; preserve the flat print faces.
    rims=[e for e in body.edges() if e.bounding_box().size.Z<1e-6]
    body=bd.chamfer(rims,length=1)
    pose=tail_placement(p);y=datums(p)['tail_y'];z=p['tail_height']
    tab=(bd.Pos(0,y+1,z)*bd.Rot(90,0,0)
         *bd.extrude(tail_key(p),amount=p['tail_key_length']))
    shape=(pose*body)+tab
    shape -= tail_cross_bore(p)
    return colored(pose.inverse()*shape,'detachable_curved_tail_DRAFT','#E9E6DC')


def motor_mount(p, side):
    gap=p['fit_gap']; iw=p['motor_width']+2*gap; il=p['motor_length']+2*gap
    w,l=iw+6,il+6; floor=p['motor_floor']; height=floor+p['motor_height']+2
    shape = box(w,l,floor) + box(3,l,height,-(iw+3)/2) + box(3,l,height,(iw+3)/2)
    shape += box(w,3,7,0,-(il+3)/2)
    shape += box(w,3,7,0,(il+3)/2)
    shape -= box(w+4,12,height,0,p['shaft_y'],floor+p['shaft_z']-4)
    for y in (-25,25):
        x=-side*(p['motor_x']-46)
        shape += box(14,14,floor,x+side*3,y)
        shape += cylinder(5,floor,x,y)
        slot=bd.SlotOverall(p['m3_clearance']+2*p['motor_adjust_y'],p['m3_clearance'],rotation=90)
        shape -= bd.Pos(x,y,-1)*bd.extrude(slot,amount=floor+2)
        # A squared rail opening removes the complete local wall segment;
        # a round clearance pocket leaves tangent feather edges in this wall.
        shape -= box(p['motor_fastener_clearance'],
                     p['motor_fastener_clearance']+2*p['motor_adjust_y'],height,x,y,floor)
    for y in (-12,8):
        for x in (-iw/2,iw/2):
            shape -= box(8,4,6,x,y,floor+1)
    return colored(shape,'motor_mount_left_DRAFT' if side<0 else 'motor_mount_right_DRAFT','#30383D')


def battery_tray(p):
    iw=p['battery_width']+2*p['fit_gap'];id=p['battery_depth']+2*p['fit_gap']
    shape=box(iw+6,id+6,2.5)+box(3,id+6,27,-(iw+3)/2)+box(3,id+6,27,(iw+3)/2)
    shape += box(iw,3,12,0,-(id+3)/2)
    shape += box(iw,3,12,0,(id+3)/2)
    # Strap through the aligned tray/base slots; removable ties avoid wide
    # mounting ears next to the larger estimated BO-motor envelopes.
    for x in (-25,25):shape -= box(3,18,5,x,0,-1)
    for x in (-(iw+3)/2,(iw+3)/2):shape -= box(8,14,4,x,0,4)
    return colored(shape,'battery_tray_DRAFT_holder_selection_pending','#30383D')


def electronics_deck(p):
    shape=box(112,42,3,0,0,23)
    for x in (-45,45):
        for y in (-12,12):
            shape += cylinder(5,23,x,y)
            shape=bore(shape,x,y,-1,28,p['m3_clearance'])
    for x in (-30,0,30):
        for y in (-9,9):shape -= box(18,3,5,x,y,22)
    return colored(shape,'electronics_deck_DRAFT_universal_tie_slots','#4E595F')


def caster_bridge(p):
    height=p['caster_height']-datums(p)['deck']
    shape=box(60,32,4,0,0,height)
    for x in (-27,27):
        shape += box(6,32,height+1,x)
        shape += box(16,16,4,x)
        shape=bore(shape,-28 if x<0 else 28,0,-1,6,p['m3_clearance'])
    for x in (-10,10):
        shape -= box(4,20,6,x,0,height-1)
    return colored(shape,'caster_bridge_DRAFT_mount_pattern_unverified','#30383D')


def sensor_bracket(p):
    shape=box(60,3,39,0,-78.5,datums(p)['deck'])+box(60,14,3,0,-73,datums(p)['deck'])
    for x in (-p['sonar_pitch']/2,p['sonar_pitch']/2):
        tool=cylinder((p['sonar_diameter']+2*p['fit_gap'])/2,12)
        tool=bd.Pos(x,-74,p['sonar_z'])*bd.Rot(90,0,0)*tool
        shape -= tool
    for x in (-25,25):shape=bore(shape,x,-72,datums(p)['deck']-1,6,p['m3_clearance'])
    return colored(shape,'sonar_bracket_DRAFT_board_retention_pending','#30383D')


def neck(p):
    t=p['wall'];h=p['neck_height']
    shape=outline(80,58,4,8)
    shape += bd.loft([octagon(52,34,6),bd.Pos(0,0,h)*octagon(46,28,5)],ruled=True)
    # Faceted cuff repeats the chest fold, within the existing flange envelope.
    shape += bd.loft([bd.Pos(0,0,z)*octagon(52-6*z/h+extra,34-6*z/h+extra,6)
                      for z,extra in ((8,3),(10,4),(14,3))],ruled=True)
    # Rear tie eyes sit outside the main cable cavity. Actual tie/cable fit is
    # pending; they are wire-tidying points, not lifting or retention handles.
    for x in (-14,14):
        eye=box(10,11,13,x,19.5,8)
        eye=bd.chamfer(eye.edges(),length=0.5)
        slot=bd.Plane.YZ*bd.SlotOverall(p['neck_tie_slot_length'],p['neck_tie_slot_width'],rotation=90)
        eye -= bd.Pos(x,22,14.5)*bd.extrude(slot,amount=6,both=True)
        shape += eye
    inside=bd.loft([bd.Pos(0,0,4)*octagon(44,26,4),bd.Pos(0,0,h-4)*octagon(38,20,3)],ruled=True)
    shape -= inside
    shape -= box(40,20,6,0,0,-1)
    shape -= box(18,12,6,0,0,h-5)
    for x in (-34,34):
        for y in (-23,23):shape=bore(shape,x,y,-1,7,p['m3_clearance'])
    for x in (-16,16):shape=bore(shape,x,0,h-5,7,p['m3_clearance'])
    return colored(shape,'fixed_neck_DRAFT_no_servo_load','#30383D')


def phone_cradle(p):
    a=datums(p);w,h,depth=a['head_width'],a['head_height'],a['head_depth']
    iw=p['phone_width']+2*p['fit_gap'];ih=p['phone_height']+2*p['fit_gap'];rim=p['phone_margin']
    shape=outline(w,h,3,8)
    shape -= box(iw-16,ih-16,6,0,0,-1)
    for x in (-(iw+rim)/2,(iw+rim)/2):
        shape += box(rim,h-rim,depth,x,-rim/2)
        shape += box(4,ih,3,x+(-rim/2-1 if x>0 else rim/2+1),0,depth-3)
    shape += box(w,rim,depth,0,-(ih+rim)/2)
    for x in (-w/2,w/2):shape -= box(24,20,depth,x,0,3)
    for x in (-80,80):shape=bore(shape,x,(ih+rim)/2,-1,6,p['m3_clearance'])
    for x in (-16,16):
        tool=bd.Pos(x,-h/2-1,8)*bd.Rot(-90,0,0)*cylinder(p['m3_clearance']/2,rim+2)
        shape -= tool
        nut=bd.extrude(bd.RegularPolygon(3.3,6),amount=2.8)
        shape -= bd.Pos(x,-ih/2-2.8,8)*bd.Rot(-90,0,0)*nut
    shape -= box(18,rim+2,10,0,-(ih+rim)/2,3)
    for x in (-47,47):
        detail=bd.Pos(x,-(ih+rim)/2,depth-0.8)*bd.extrude(bd.SlotOverall(34,1.6),amount=1.5)
        shape -= detail
    shape &= outline(w,h,depth+1,6)
    return colored(shape,'phone_cradle_DRAFT_camera_case_fit_pending','#E9E6DC')


def phone_cap(p):
    a=datums(p);h,depth,w=a['head_height'],a['head_depth'],a['head_width'];rim=p['phone_margin']
    y=h/2-rim/2
    shape=box(w-0.8,rim-0.6,depth-3.4,0,y,3.4) & outline(w,h,depth+1,6)
    for side in (-1,1):
        profile=bd.Polygon((side*66,h/2-2),(side*87,h/2-2),
                           (side*85,h/2+10),(side*83,h/2+13),
                           (side*80,h/2+13),align=None)
        ear=bd.Pos(0,0,3.4)*bd.extrude(profile,amount=depth-3.4,dir=(0,0,1))
        front=[e for e in ear.edges() if abs(e.center().Z-depth)<1e-6]
        ear=bd.chamfer(front,length=0.7)
        inset=bd.Polygon((side*73,h/2+1),(side*83,h/2+1),
                         (side*82,h/2+8),align=None)
        ear -= bd.Pos(0,0,depth-1)*bd.extrude(inset,amount=2,dir=(0,0,1))
        shape += ear
    for x in (-80,80):shape=bore(shape,x,y,2,depth+2,p['m3_clearance'])
    return colored(shape,'phone_top_cap_DRAFT_passive_cat_corners','#E9E6DC')


def hardware_envelopes(p):
    """Generic view/clearance geometry, never a purchasable or printed part."""
    a=datums(p);result=[]
    for side in (-1,1):
        tire=bd.Pos(side*p['wheel_x'],a['wheel_y'],a['axle_z'])*bd.Rot(0,90,0)*bd.Cylinder(p['wheel_diameter']/2,p['wheel_width'])
        result.append(colored(tire,'REFERENCE_ONLY_wheel_envelope_'+str(side),'#20272C'))
        motor=box(p['motor_width'],p['motor_length'],p['motor_height'],side*p['motor_x'],p['motor_y'],a['deck']+p['motor_floor'])
        result.append(colored(motor,'REFERENCE_ONLY_motor_envelope_'+str(side),'#D6B252'))
    holder=box(p['battery_width'],p['battery_depth'],p['battery_height'],0,p['battery_y'],a['deck']+2.5)
    result.append(colored(holder,'REFERENCE_ONLY_AA_holder_NOT_SELECTED','#56634D'))
    phone=box(p['phone_width'],p['phone_height'],p['phone_thickness'],0,0,3+p['fit_gap'])
    phone=bd.Pos(0,8,a['head_bottom']+a['head_height']/2)*bd.Rot(90,0,0)*phone
    result.append(colored(phone,'REFERENCE_ONLY_phone_case_envelope','#11191E'))
    for x in (-37,37):
        eye=bd.Pos(x,-(3+p['fit_gap']+p['phone_thickness'])+7.5,a['head_bottom']+a['head_height']/2)*bd.Rot(90,0,0)*bd.extrude(bd.RectangleRounded(24,19,6),amount=0.4)
        result.append(colored(eye,'REFERENCE_ONLY_display_graphic_'+str(x),'#69E2DB'))
    ball=bd.Pos(0,p['caster_y'],8)*bd.Sphere(8)
    housing=box(30,28,p['caster_height']-14,0,p['caster_y'],14)
    result.append(colored(ball+housing,'REFERENCE_ONLY_caster_envelope','#56636A'))
    for x in (-p['sonar_pitch']/2,p['sonar_pitch']/2):
        can=bd.Pos(x,-79,p['sonar_z'])*bd.Rot(90,0,0)*cylinder(p['sonar_diameter']/2,12)
        result.append(colored(can,'REFERENCE_ONLY_sonar_can_'+str(x),'#A4AFB5'))
    return bd.Compound(children=result,label='REFERENCE_ONLY_bought_items_and_display_graphics')
