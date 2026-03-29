# Agentic Security System

A comprehensive security system for detecting anomalies in processes, files, and network activity using machine learning models.

## Project Structure

```
agentic_security_system/
├── data/                 # Data files (raw, processed, temporary)
├── models/              # Model definitions and saved weights
│   ├── process_model/   # Process anomaly detection
│   ├── file_model/      # File anomaly detection
│   ├── network_model/   # Network anomaly detection
│   └── aggregator_model/# Ensemble model
├── src/                 # Source code
│   ├── data_processing/ # Data loading and splitting
│   ├── feature_engineering/ # Feature extraction
│   ├── inference/       # Inference pipeline
│   ├── aggregation/     # Aggregation logic
│   └── utils/           # Utility functions
├── configs/             # Configuration files
├── notebooks/           # Jupyter notebooks for analysis
├── tests/               # Unit tests
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the system:
- Edit `configs/model_config.yaml` for model settings
- Edit `configs/thresholds.yaml` for anomaly detection thresholds
- Edit `configs/system_config.yaml` for system settings

## Usage

```bash
python main.py
```

## Models

- **Process Model**: Detects anomalous process behavior using Isolation Forest and XGBoost
- **File Model**: Detects suspicious file operations using CatBoost
- **Network Model**: Detects network anomalies using Isolation Forest and XGBoost
- **Aggregator Model**: Ensemble model combining predictions from all three models

## Features

- Multi-model ensemble approach
- Real-time inference pipeline
- Event aggregation and correlation
- Configurable thresholds and parameters

## Testing

Run tests with:
```bash
pytest tests/
```

## License

Proprietary
