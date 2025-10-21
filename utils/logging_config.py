"""
Logging configuration to suppress verbose output from libraries
and show only pipeline-relevant logs.
"""

import logging
import warnings
import os


def setup_logging():
    """
    Configure logging to suppress verbose library output.
    Shows only: tqdm progress bars, dataset loading, and reader/worker logs.
    """

    # Suppress Python warnings
    warnings.filterwarnings("ignore")

    # Set environment variables FIRST before any imports
    os.environ["NEMO_LOGGING_LEVEL"] = "ERROR"
    os.environ["HYDRA_FULL_ERROR"] = "0"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["DATASETS_VERBOSITY"] = "error"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["HF_HUB_VERBOSITY"] = "error"

    # Configure root logger to only show ERROR and above
    logging.basicConfig(
        level=logging.CRITICAL,
        format='%(message)s',
        force=True
    )

    # Suppress NeMo verbose logging (try multiple logger names)
    for logger_name in ["nemo_logger", "nemo", "NeMo", "nemo_logger.nemo_logging"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False
        # Remove all handlers
        logger.handlers = []

    # Suppress PyTorch Lightning logging
    for logger_name in ["pytorch_lightning", "lightning", "lightning_fabric"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False

    # Suppress HuggingFace datasets logging
    for logger_name in ["datasets", "datasets.builder", "datasets.info"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False

    # Suppress transformers logging
    logging.getLogger("transformers").setLevel(logging.CRITICAL)

    # Suppress filelock logging
    logging.getLogger("filelock").setLevel(logging.CRITICAL)

    # Suppress other common verbose loggers
    for logger_name in ["urllib3", "requests", "fsspec", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)