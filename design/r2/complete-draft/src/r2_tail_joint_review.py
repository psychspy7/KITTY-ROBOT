"""Exploded, view-only pair to explain removal toward the rear (+Y)."""
from cadgen import build123d as bd, step
from settings import load, datums, tail_placement
from r2_cover_rear import r2_cover_rear
from r2_tail import r2_tail


@step(out='../STEP/r2_tail_joint_review.step')
def r2_tail_joint_review():
    p=load()
    return bd.Compound(children=[
        bd.Pos(0,0,datums(p)['deck'])*r2_cover_rear(),
        bd.Pos(0,35,0)*tail_placement(p)*r2_tail(),
    ],label='VIEW_ONLY_tail_pulled_rearward_35mm_remove_cross_screw_first')


if __name__=='__main__':
    r2_tail_joint_review()
