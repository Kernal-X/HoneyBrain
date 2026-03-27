<<<<<<< HEAD
"""
Main Entry Point
Agentic Security System
"""

import yaml
from src.inference.pipeline import InferencePipeline


def load_config(config_file):
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    """Main entry point"""
    # Load configurations
    model_config = load_config('configs/model_config.yaml')
    threshold_config = load_config('configs/thresholds.yaml')
    system_config = load_config('configs/system_config.yaml')
    
    # Initialize inference pipeline
    pipeline = InferencePipeline()
    
    # TODO: Implement main logic
    print("Agentic Security System Started")
    print(f"Version: {system_config['system']['version']}")


if __name__ == '__main__':
    main()
=======
from agents.system_agent import SystemAgent

def run():
    agent = SystemAgent()
    agent.start()

if __name__ == "__main__":
    run()
>>>>>>> cb645a8f52bb31144c71a23275e733ff461db612
