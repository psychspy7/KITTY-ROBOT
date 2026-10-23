"""Build STEP models, export conforming OCCT STL meshes, then verify them."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def main():
    os.environ.setdefault('CADGEN_CACHE_DIR',str(ROOT/'tmp'/'cad-cache'))
    os.environ.setdefault('CADGEN_DAEMON','0')
    subprocess.run([sys.executable,str(ROOT/'src'/'v7_complete_draft.py')],cwd=ROOT,check=True)
    from cadgen import read_step,build123d as bd
    sys.path.insert(0,str(ROOT/'checks'))
    from verify_exports import PARTS,main as verify
    (ROOT/'STL').mkdir(exist_ok=True)
    for name in [*PARTS,'v7_printed_assembly','v7_complete_draft']:
        shape=read_step(ROOT/'STEP'/(name+'.step'))
        if not bd.export_stl(shape,str(ROOT/'STL'/(name+'.stl')),tolerance=0.003,angular_tolerance=0.05):
            raise RuntimeError('OCCT STL export failed: '+name)
        print('Exported STL:',name,flush=True)
    verify()


if __name__=='__main__':main()
