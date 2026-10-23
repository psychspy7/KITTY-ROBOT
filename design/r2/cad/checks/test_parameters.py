import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parameters import ParameterError, validate


class ParametersTests(unittest.TestCase):
    def setUp(self):
        self.example = json.loads((ROOT / 'parameters.example.json').read_text())

    def test_draft_fixture_is_valid_but_cannot_be_verified_input(self):
        validate(self.example, require_measured=False)
        with self.assertRaises(ParameterError):
            validate(self.example, require_measured=True)

    def test_missing_measurements_report_actual_fields(self):
        data = copy.deepcopy(self.example)
        data['kind'] = 'measured'
        data['dimensions']['phone_width_mm'] = None
        with self.assertRaisesRegex(ParameterError, 'phone_width_mm'):
            validate(data, require_measured=True)

    def test_nonfinite_or_negative_dimensions_are_rejected(self):
        for value in [float('nan'), -1, True]:
            data = copy.deepcopy(self.example)
            data['dimensions']['motor_width_mm'] = value
            with self.assertRaises(ParameterError):
                validate(data, require_measured=False)

    def test_measured_values_need_individual_evidence(self):
        data = copy.deepcopy(self.example)
        data['kind'] = 'measured'
        with self.assertRaisesRegex(ParameterError, 'evidence'):
            validate(data, require_measured=True)

    def test_phone_and_base_must_fit_printer_in_export_orientation(self):
        data = copy.deepcopy(self.example)
        data['dimensions']['printer_x_mm'] = 100
        with self.assertRaisesRegex(ParameterError, 'printer'):
            validate(data, require_measured=False)


if __name__ == '__main__':
    unittest.main()
