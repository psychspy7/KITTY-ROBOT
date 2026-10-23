import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain import MissionBrain, Observation


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.brain = MissionBrain(clock=self.clock)
        self.seq = 0

    def feed(self, **changes):
        self.seq += 1
        values = dict(sequence=self.seq, captured_at=self.clock(),
                      received_at=self.clock(), center_x=0.0, confidence=0.95,
                      front_range_m=1.0, target_range_m=2.0, source='fixture')
        values.update(changes)
        self.brain.heartbeat()
        return self.brain.observe(Observation(**values))

    def arm(self, **changes):
        self.feed(**changes)
        self.assertTrue(self.brain.arm_preview())
        return self.brain.snapshot()

    def assertStopped(self, state):
        self.assertEqual(state['command']['linear_m_s'], 0)
        self.assertEqual(state['command']['angular_rad_s'], 0)
        self.assertFalse(state['hardware_enabled'])

    def test_initial_state_is_disarmed_and_transport_absent(self):
        state = self.brain.snapshot()
        self.assertEqual(state['mode'], 'DISARMED')
        self.assertEqual(state['transport'], 'not_implemented')
        self.assertStopped(state)
        self.assertFalse(self.brain.arm_preview())

    def test_centered_target_gives_bounded_preview_only(self):
        state = self.arm()
        self.assertEqual(state['mode'], 'APPROACHING')
        self.assertGreater(state['command']['linear_m_s'], 0)
        self.assertLessEqual(state['command']['linear_m_s'], 0.12)
        self.assertFalse(state['hardware_enabled'])

    def test_alignment_does_not_also_move_forward(self):
        state = self.arm(center_x=0.8)
        self.assertEqual(state['mode'], 'ALIGNING')
        self.assertEqual(state['command']['linear_m_s'], 0)
        self.assertLess(state['command']['angular_rad_s'], 0)
        self.assertLessEqual(abs(state['command']['angular_rad_s']), 0.5)

    def test_front_obstacle_latches_until_explicit_rearm(self):
        self.arm()
        self.feed(front_range_m=0.1)
        self.assertStopped(self.brain.snapshot())
        self.feed(front_range_m=1)
        state = self.brain.snapshot()
        self.assertEqual(state['mode'], 'FAULT')
        self.assertFalse(state['armed'])
        self.assertTrue(self.brain.arm_preview())

    def test_stale_frame_stops_and_new_frame_does_not_rearm(self):
        self.arm()
        self.clock.now += 0.4
        self.brain.heartbeat()
        state = self.brain.snapshot()
        self.assertEqual(state['reason'], 'stale_frame')
        self.assertStopped(state)
        self.feed()
        self.assertEqual(self.brain.snapshot()['mode'], 'FAULT')

    def test_lost_heartbeat_stops_with_a_fresh_frame(self):
        self.arm()
        self.clock.now += 0.4
        self.seq += 1
        self.brain.observe(Observation(self.seq, self.clock(), self.clock(), 0, .95, 1, 2, 'fixture'))
        state = self.brain.snapshot()
        self.assertEqual(state['reason'], 'lost_link')
        self.assertStopped(state)

    def test_estop_cannot_be_released_by_arm_or_new_frames(self):
        self.arm()
        self.brain.estop()
        self.feed()
        self.assertFalse(self.brain.arm_preview())
        self.assertEqual(self.brain.snapshot()['mode'], 'ESTOP')
        self.brain.reset_estop()
        self.assertEqual(self.brain.snapshot()['mode'], 'DISARMED')
        self.assertFalse(self.brain.arm_preview())
        self.arm()

    def test_sonar_range_is_not_target_arrival(self):
        state = self.arm(front_range_m=0.4, target_range_m=None)
        self.assertNotEqual(state['mode'], 'ARRIVED')
        self.assertEqual(state['mode'], 'APPROACHING')
        self.feed(target_range_m=0.3)
        self.assertEqual(self.brain.snapshot()['mode'], 'ARRIVED')
        self.assertStopped(self.brain.snapshot())

    def test_invalid_and_replayed_frames_revoke_motion(self):
        for changes in [dict(center_x=math.nan), dict(confidence=math.inf),
                        dict(confidence=0.1), dict(front_range_m=None),
                        dict(front_range_m=-1), dict(target_range_m=math.nan),
                        dict(captured_at=101), dict(source='invented')]:
            with self.subTest(changes=changes):
                self.brain = MissionBrain(clock=self.clock)
                self.arm()
                self.feed(**changes)
                self.assertStopped(self.brain.snapshot())
                self.assertEqual(self.brain.snapshot()['mode'], 'FAULT')
        self.brain = MissionBrain(clock=self.clock)
        self.arm()
        self.seq -= 1
        self.assertFalse(self.feed())
        self.assertEqual(self.brain.snapshot()['reason'], 'replayed_frame')

    def test_disarm_revokes_preview_and_chat_never_arms(self):
        self.arm()
        self.brain.disarm()
        self.assertStopped(self.brain.snapshot())
        self.assertIn('preview', self.brain.chat('move forward').lower())
        self.assertFalse(self.brain.snapshot()['armed'])
        self.assertIn('camera', self.brain.chat('what do you see?').lower())


if __name__ == '__main__':
    unittest.main()
