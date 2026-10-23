from cadgen import build123d as bd, step
from v3_printed_assembly import v3_printed_assembly
from v3_reference_hardware import v3_reference_hardware


@step(out='../STEP/v3_complete_draft.step')
def v3_complete_draft():
    return bd.Compound(children=[v3_printed_assembly(),v3_reference_hardware()],
                       label='V3_COMPLETE_DRAFT_VIEW_ONLY_INCLUDES_HARDWARE_ENVELOPES')


if __name__=='__main__':
    v3_complete_draft()
