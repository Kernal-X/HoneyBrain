import time

from langgraph_pipeline import LangGraphSecurityPipeline


class SystemAgent:
    def __init__(self):
        self.pipeline = LangGraphSecurityPipeline()
        self.state = {"deployment": {}}

    def start(self):
        try:
            while True:
                self.state = self.pipeline.run_monitor_cycle(self.state)
                time.sleep(0.1)

        except KeyboardInterrupt:
            return
