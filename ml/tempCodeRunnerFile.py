================
class Pipeline:

    def __init__(self):
        self.router = ModelRouter()
        self.aggregator = StreamingAggregator(threshold=1.5, decay=0.9)

        print("✅ Pipeline Initialized")