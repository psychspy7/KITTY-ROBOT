from cadgen import build123d as bd, step
from v7_printed_assembly import v7_printed_assembly
from v7_reference_hardware import v7_reference_hardware


@step(out='../STEP/v7_complete_draft.step')
def v7_complete_draft():
    return bd.Compound(children=[v7_printed_assembly(),v7_reference_hardware()],
                       label='V7_COMPLETE_DRAFT_VIEW_ONLY_INCLUDES_HARDWARE_ENVELOPES')


if __name__=='__main__':
    v7_complete_draft()
