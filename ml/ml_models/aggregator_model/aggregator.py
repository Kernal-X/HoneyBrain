import datetime
import time
import json
from collections import Counter, deque


class Aggregator:

    def __init__(self, window_size=10):
        self.events_buffer = deque()
        self.window_size = window_size

    # -------- Add event to buffer --------
    def add_event(self, event):
        current_time = time.time()

        event["ts"] = current_time
        self.events_buffer.append(event)

        # remove old events
        while self.events_buffer and (current_time - self.events_buffer[0]["ts"] > self.window_size):
            self.events_buffer.popleft()

    # -------- Build state from buffer --------
    def build_state_from_buffer(self):
        events = list(self.events_buffer)

        if not events:
            return None

        return self.build_state(events)

    # -------- Base risk --------
    def base_risk(self, events):
        scores = [e["risk_score"] for e in events]
        return max(scores)

    # -------- Multi-model boost --------
    def multi_model_boost(self, events):
        types = set(e["type"] for e in events)
        return 0.1 * len(types)

    # -------- Frequency boost --------
    def frequency_boost(self, events):
        count = len(events)

        if count > 5:
            return 0.2
        elif count > 3:
            return 0.1
        else:
            return 0.0

    # -------- Diversity boost --------
    def diversity_boost(self, events):
        types = [e["type"] for e in events]
        freq = Counter(types)

        if any(v >= 3 for v in freq.values()):
            return 0.15

        return 0.0

    # -------- Final risk --------
    def compute_final_risk(self, events):

        base = self.base_risk(events)
        multi = self.multi_model_boost(events)
        freq = self.frequency_boost(events)
        diversity = self.diversity_boost(events)

        final = base + multi + freq + diversity

        return min(final, 1.0)

    # -------- Severity --------
    def get_severity(self, score):
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"

    # -------- Build final state --------
    def build_state(self, events):

        final_risk = self.compute_final_risk(events)
        severity = self.get_severity(final_risk)

        state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "risk_score": round(final_risk, 3),
            "severity": severity,
            "events": events
        }

        return state