#!/usr/bin/env python3
"""
Nano Codec Audio Processing Pipeline

This script processes HuggingFace audio datasets using NVIDIA's NeMo Nano Codec model.
It uses a multi-GPU, multi-process architecture to efficiently encode audio data.

Configuration is read from config.yaml.
"""

from utils.logging_config import setup_logging
from utils.pipeline_manager import PipelineManager


if __name__ == "__main__":
    # Setup logging to suppress verbose library output
    setup_logging()

    # Create and run the pipeline
    pipeline = PipelineManager(config_path="config.yaml")
    pipeline.run()
