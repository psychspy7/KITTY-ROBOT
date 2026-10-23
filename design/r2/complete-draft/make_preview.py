"""Embed the built STLs in one offline HTML viewer. Geometry is unchanged."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parent
MODELS=[
    ('r2_complete_draft','Complete robot','Whole-robot preview including generic bought-component envelopes and display graphics. VIEW ONLY; do not slice this assembled file.'),
    ('r2_printed_assembly','Printed assembly','All 12 proposed printed pieces in their assembled positions. VIEW ONLY; use the separate part files for manufacturing review.'),
    ('r2_base','Base chassis','Chassis, shared mounting bores, caster passage and battery strap slots.'),
    ('r2_cover_front','Front cover','Faceted front body half with a sonar opening and cover fasteners.'),
    ('r2_cover_rear','Rear cover','Rear half with ventilation and provisional service openings.'),
    ('r2_motor_left','Left motor mount','Channel for the reported 61 × 20 mm motor envelope. Height, shaft and hub geometry still need measurement.'),
    ('r2_motor_right','Right motor mount','Mirrored mounting feet. Height, shaft and hub geometry still need measurement.'),
    ('r2_battery_tray','Battery tray','Low tray and strap paths around an assumed holder. AA chemistry, cell count and holder are not selected.'),
    ('r2_electronics_deck','Electronics deck','Raised universal tie-slot deck; exact board footprints and cable routes remain unverified.'),
    ('r2_caster_bridge','Caster bridge','Raised support above the chassis passage. Actual caster ownership, height and fastening still need confirmation.'),
    ('r2_sensor_bracket','Sensor bracket','Front transducer face and chassis foot. Actual HC-SR04 board retention and fit still need checking.'),
    ('r2_neck','Fixed neck','Broad fixed support with a cable passage and head fasteners. No servo phone load is assumed.'),
    ('r2_phone_cradle','Phone cradle','Uses your 164 × 76 × 8 mm phone envelope. Confirm case, padding, camera and access before printing.'),
    ('r2_phone_cap','Phone retainer','Removable upper retainer with passive cat corners and two screw bores.'),
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots',type=Path,default=ROOT/'tmp'/'snapshots')
    parser.add_argument('--out',type=Path,default=ROOT/'tmp'/'KITTY-R2-COMPLETE-VIEWER.html')
    args=parser.parse_args();models=[]
    for stem,label,note in MODELS:
        data=(ROOT/'STL'/(stem+'.stl')).read_bytes();n=struct.unpack_from('<I',data,80)[0]
        assert len(data)==84+n*50
        low=[float('inf')]*3;high=[-float('inf')]*3
        for i in range(n):
            values=struct.unpack_from('<12fH',data,84+50*i)
            for j in (3,6,9):
                for axis in range(3):
                    low[axis]=min(low[axis],values[j+axis]);high[axis]=max(high[axis],values[j+axis])
        image_name={'r2_complete_draft':'assembly-iso','r2_printed_assembly':'printed-assembly'}.get(stem,stem)
        png=args.snapshots/(image_name+'.png')
        models.append({'stem':stem,'label':label,'note':note,'triangles':n,
                       'dimensions':[round(b-a,3) for a,b in zip(low,high)],
                       'sha256':hashlib.sha256(data).hexdigest(),
                       'stl':base64.b64encode(data).decode(),
                       'image':'data:image/png;base64,'+base64.b64encode(png.read_bytes()).decode() if png.exists() else ''})
    template=(ROOT/'viewer-template.html.in').read_text()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(template.replace('__MODEL_DATA__',json.dumps(models,separators=(',',':'))))
    print(json.dumps({'viewer':str(args.out),'models':len(models),'bytes':args.out.stat().st_size}))


if __name__=='__main__':main()
