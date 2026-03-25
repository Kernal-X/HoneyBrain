from sklearn.ensemble import IsolationForest


class NetworkModel:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        self.min_score = None
        self.max_score = None

    def train(self, X):
        self.model.fit(X)

    def compute_scores(self, X):
        scores = -self.model.decision_function(X)
        return scores

    def normalize_scores(self, scores):
        if self.min_score is None:
            self.min_score = scores.min()
            self.max_score = scores.max()

        normalized = (scores - self.min_score) / (self.max_score - self.min_score + 1e-8)
        return normalized

    def predict(self, X):
        raw_scores = self.compute_scores(X)
        norm_scores = self.normalize_scores(raw_scores)
        return norm_scores