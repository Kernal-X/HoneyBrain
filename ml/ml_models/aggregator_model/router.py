from ml_models.file_model.file_model import FileModel
from ml_models.network_model.network_model import NetworkModel
from ml_models.process_model.process_model import ProcessModel


class ModelRouter:

    def __init__(self):
        self.file_model = FileModel("ml_models/file_model/file_hybrid_final.pkl")
        self.network_model = NetworkModel("ml_models/network_model/network_hybrid_model.pkl")
        self.process_model = ProcessModel("ml_models/process_model/process_hybrid_final.pkl")

        self.models = {
            "file": self.file_model,
            "network": self.network_model,
            "process": self.process_model
        }

    def route(self, event):

        model = self.models.get(event["type"])

        if not model:
            return {
                "risk_score": 0.0,
                "event": {
                    "type": event["type"],
                    "risk_score": 0.0,
                    "data": {"reason": "no model found"}
                }
            }

        return model.predict(event)