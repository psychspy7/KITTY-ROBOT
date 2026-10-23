"""Build, export and verify the four separately supplied first-print samples."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def main():
    os.environ.setdefault('CADGEN_CACHE_DIR',str(ROOT/'tmp/cad-cache'))
    os.environ.setdefault('CADGEN_DAEMON','0')
    sys.path.insert(0,str(ROOT/'checks'))
    from verify_fit_samples import FIT_PARTS,main as verify
    from cadgen import read_step,build123d as bd
    (ROOT/'STL').mkdir(exist_ok=True)
    for name in FIT_PARTS:
        subprocess.run([sys.executable,str(ROOT/'src'/(name+'.py'))],cwd=ROOT,check=True)
        shape=read_step(ROOT/'STEP'/(name+'.step'))
        if not bd.export_stl(shape,str(ROOT/'STL'/(name+'.stl')),tolerance=0.003,angular_tolerance=0.05):
            raise RuntimeError('Sample export failed: '+name)
    verify()


if __name__=='__main__':main()
