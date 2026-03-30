import time
import datetime


class StreamingAggregator:

    def __init__(self, threshold=1.5, decay=0.9):
        self.threshold = threshold
        self.decay = decay

        self.aggregator_score = 0.0
        self.event_queue = []

    # -------- Add event --------
    def add_event(self, event):
        """
        event = {
            "type": "network",
            "risk_score": 0.7,
            "data": {...}
        }
        """

        # Add timestamp
        event["timestamp"] = time.time()

        # Store event
        self.event_queue.append(event)

        # Update score
        self.update_score(event["risk_score"])

        # Build current state
        state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "current_score": round(self.aggregator_score, 3),
            "num_events": len(self.event_queue)
        }

        # -------- Trigger condition --------
        if self.aggregator_score >= self.threshold:
            output = self.build_output()

            result = {
                "state": state,
                "alert": True,
                "data": output
            }

            self.reset()
            return result

        # -------- No trigger --------
        return {
            "state": state,
            "alert": False
        }


    # -------- Score update --------
    def update_score(self, risk_score):
        """
        Decay-based accumulation:
        new_score = decay * old_score + current_risk
        """
        self.aggregator_score = (
            self.decay * self.aggregator_score + risk_score
        )

    # -------- Build final output --------
    def build_output(self):

        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "aggregated_risk": round(self.aggregator_score, 3),
            "num_events": len(self.event_queue),
            "events": [
                {
                    "type": e["type"],
                    "risk_score": round(e["risk_score"], 3),
                    "data": e["data"]
                }
                for e in self.event_queue
            ]
        }

    # -------- Reset after alert --------
    def reset(self):
        self.aggregator_score = 0.0
        self.event_queue = []