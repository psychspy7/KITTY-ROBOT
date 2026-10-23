from cadgen import build123d as bd, step
from r2_printed_assembly import r2_printed_assembly
from r2_reference_hardware import r2_reference_hardware


@step(out='../STEP/r2_complete_draft.step')
def r2_complete_draft():
    return bd.Compound(children=[r2_printed_assembly(),r2_reference_hardware()],
                       label='R2_COMPLETE_DRAFT_VIEW_ONLY_INCLUDES_HARDWARE_ENVELOPES')


if __name__=='__main__':
    r2_complete_draft()
