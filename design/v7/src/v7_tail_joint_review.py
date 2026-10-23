"""Exploded, view-only pair to explain removal toward the rear (+Y)."""
from cadgen import build123d as bd, step
from settings import load, datums, tail_placement
from v7_cover_rear import v7_cover_rear
from v7_tail import v7_tail


@step(out='../STEP/v7_tail_joint_review.step')
def v7_tail_joint_review():
    p=load()
    return bd.Compound(children=[
        bd.Pos(0,0,datums(p)['deck'])*v7_cover_rear(),
        bd.Pos(0,35,0)*tail_placement(p)*v7_tail(),
    ],label='VIEW_ONLY_tail_pulled_rearward_35mm_remove_cross_screw_first')


if __name__=='__main__':
    v7_tail_joint_review()
