import unittest
from brain import RobotBrain

class TestHandoffRegressions(unittest.TestCase):
    def test_explicit_reset_phrases_clear_simulator_stop(self):
        for phrase in ('reset emergency stop', 'release emergency stop', 'reset safety stop'):
            with self.subTest(phrase=phrase):
                b=RobotBrain();b.action('estop');b.chat(phrase)
                self.assertEqual(b.safety,'READY')
                self.assertEqual(b.mode,'IDLE')

    def test_reset_substring_does_not_release_stop(self):
        b=RobotBrain();b.action('estop')
        b.chat('do not reset emergency stop')
        self.assertEqual(b.safety,'EMERGENCY STOP')

    def test_stop_phrase_still_latches(self):
        b=RobotBrain();b.action('forward');b.chat('emergency stop')
        self.assertEqual(b.safety,'EMERGENCY STOP')
        self.assertIsNone(b.manual)
