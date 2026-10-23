"""Deterministic mission preview. No hardware transport or motor I/O exists here.

Times are monotonic seconds in the receiving process, distances are metres,
image centre is -1 (left) to +1 (right), positive angular velocity turns left.
A caller sharing a brain between threads must hold its own lock.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Callable


@dataclass(frozen=True)
class Observation:
    sequence: int
    captured_at: float
    received_at: float
    center_x: float
    confidence: float
    front_range_m: float | None
    target_range_m: float | None
    source: str


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


class MissionBrain:
    FRAME_TIMEOUT_S = 0.3
    LINK_TIMEOUT_S = 0.3
    MAX_LINEAR_M_S = 0.12
    MAX_ANGULAR_RAD_S = 0.5
    OBSTACLE_STOP_M = 0.25
    TARGET_ARRIVAL_M = 0.45

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self.armed = False
        self.estop_latched = False
        self.mode = 'DISARMED'
        self.reason = 'not_armed'
        self.observation = None
        self.last_sequence = -1
        self.last_heartbeat = None
        self.bad_frame_reason = None
        self.linear = self.angular = 0.0

    def heartbeat(self):
        self.last_heartbeat = self.clock()

    def _fault(self, reason):
        self.armed = False
        self.linear = self.angular = 0.0
        if not self.estop_latched:
            self.mode, self.reason = 'FAULT', reason

    def observe(self, obs: Observation):
        now = self.clock()
        reason = None
        if type(obs.sequence) is not int or obs.sequence <= self.last_sequence:
            reason = 'replayed_frame'
        elif (not finite(obs.captured_at) or not finite(obs.received_at)
              or obs.captured_at > obs.received_at or obs.received_at > now):
            reason = 'invalid_timestamp'
        elif (not finite(obs.center_x) or not -1 <= obs.center_x <= 1
              or not finite(obs.confidence) or not 0.65 <= obs.confidence <= 1):
            reason = 'target_unreliable'
        elif not finite(obs.front_range_m) or obs.front_range_m <= 0:
            reason = 'range_invalid'
        elif obs.target_range_m is not None and (not finite(obs.target_range_m) or obs.target_range_m <= 0):
            reason = 'target_range_invalid'
        elif obs.source not in ('fixture', 'camera'):
            reason = 'source_invalid'
        if reason:
            self.bad_frame_reason = reason
            if self.armed:
                self._fault(reason)
            return False
        self.observation = obs
        self.last_sequence = obs.sequence
        self.bad_frame_reason = None
        self.step()
        return True

    def _unsafe_reason(self):
        if self.bad_frame_reason:
            return self.bad_frame_reason
        if self.observation is None:
            return 'missing_frame'
        now = self.clock()
        if now - self.observation.captured_at > self.FRAME_TIMEOUT_S:
            return 'stale_frame'
        if self.last_heartbeat is None or now - self.last_heartbeat > self.LINK_TIMEOUT_S:
            return 'lost_link'
        if self.observation.front_range_m <= self.OBSTACLE_STOP_M:
            return 'obstacle'
        return None

    def arm_preview(self):
        """Arm a mathematical preview only; this never enables physical output."""
        if self.estop_latched:
            return False
        reason = self._unsafe_reason()
        if reason:
            self.reason = reason
            return False
        self.armed = True
        self.step()
        return True

    def disarm(self):
        self.armed = False
        self.linear = self.angular = 0.0
        self.mode, self.reason = 'DISARMED', 'operator_disarm'
        if self.estop_latched:
            self.mode, self.reason = 'ESTOP', 'operator_estop'

    def estop(self):
        self.estop_latched = True
        self.disarm()

    def reset_estop(self):
        self.estop_latched = False
        self.observation = None
        self.last_heartbeat = None
        self.bad_frame_reason = None
        self.disarm()

    def step(self):
        self.linear = self.angular = 0.0
        if self.estop_latched or not self.armed:
            return
        reason = self._unsafe_reason()
        if reason:
            self._fault(reason)
            return
        obs = self.observation
        if obs.target_range_m is not None and obs.target_range_m <= self.TARGET_ARRIVAL_M:
            self.armed = False
            self.mode, self.reason = 'ARRIVED', 'target_range_reached'
        elif abs(obs.center_x) > 0.12:
            self.mode, self.reason = 'ALIGNING', 'target_off_center'
            self.angular = -obs.center_x * self.MAX_ANGULAR_RAD_S
        else:
            self.mode, self.reason = 'APPROACHING', 'target_centered'
            self.linear = self.MAX_LINEAR_M_S

    def snapshot(self):
        self.step()
        obs = self.observation
        face = {'ESTOP': 'alert', 'FAULT': 'alert', 'ALIGNING': 'focused',
                'APPROACHING': 'focused', 'ARRIVED': 'happy'}.get(self.mode, 'idle')
        return {
            'mode': self.mode, 'reason': self.reason, 'armed': self.armed,
            'estop_latched': self.estop_latched, 'hardware_enabled': False,
            'transport': 'not_implemented', 'face': face,
            'source': obs.source if obs else 'none',
            'frame_age_ms': round((self.clock() - obs.captured_at) * 1000) if obs else None,
            'command': {'linear_m_s': self.linear, 'angular_rad_s': self.angular,
                        'valid_for_ms': 150, 'preview_only': True},
            'observation': None if not obs else {
                'sequence': obs.sequence, 'center_x': obs.center_x,
                'confidence': obs.confidence, 'front_range_m': obs.front_range_m,
                'target_range_m': obs.target_range_m,
            },
        }

    def chat(self, text):
        """Offline personality; conversational text is never an action channel."""
        low = text.strip().lower()
        state = self.snapshot()
        if any(word in low for word in ('forward', 'drive', 'move', 'stop', 'turn', 'arm')):
            return 'Use the explicit preview controls for movement or stop tests. Chat never sends motor commands.'
        if any(word in low for word in ('see', 'camera', 'look', 'detect')):
            return ('No live camera is connected here. Any target/range shown is a labelled developer fixture; '
                    'real vision and measured sensors still need integration.')
        if any(word in low for word in ('status', 'doing', 'where')):
            return f"Preview state: {state['mode']}; reason: {state['reason']}. Physical motor output is disabled."
        if any(word in low for word in ('who', 'name', 'built', 'made')):
            return 'I am KITTY, the Kitty Sentinel companion from Team Prometheus. My current workspace is a software preview.'
        if any(word in low for word in ('joke', 'funny')):
            return 'My wheels are currently a mathematical possibility. Excellent fuel economy.'
        if not low:
            return 'Ask about my status, camera setup or the next bench check.'
        return ('Ready for the next small, verified step. This offline personality handles status and a few replies; '
                'an open-ended language model is not connected.')
