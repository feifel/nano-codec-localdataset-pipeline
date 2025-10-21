from datasets import load_dataset, Audio, disable_progress_bars
from typing import Dict, Any
from utils.config_manager import DatasetConfig

# Disable HuggingFace progress bars globally
disable_progress_bars()


class DatasetProcessor:
    """Handles loading and preprocessing of HuggingFace datasets"""

    def __init__(self, dataset_config: DatasetConfig, sample_rate: int = 22050):
        self.config = dataset_config
        self.sample_rate = sample_rate
        self.dataset = None

    def load_dataset(self, num_proc: int = 5) -> None:
        """Load dataset from HuggingFace"""
        dataset_desc = f"{self.config.name}"
        if self.config.sub_name:
            dataset_desc += f" ({self.config.sub_name})"
        dataset_desc += f" [{self.config.split}]"

        print(f"📦 Loading dataset: {dataset_desc}")

        self.dataset = load_dataset(
            self.config.name,
            self.config.sub_name,  # Can be None
            num_proc=num_proc,
            split=self.config.split,
            verification_mode='no_checks',  # Skip verification to reduce logs
            trust_remote_code=True  # Allow datasets with custom code
        ).cast_column(self.config.audio_column_name, Audio(self.sample_rate))

        print(f"  ✅ Loaded {len(self.dataset)} samples from {dataset_desc}")

    def get_dataset(self):
        """Get the loaded dataset"""
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_dataset() first.")
        return self.dataset

    def prepare_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a single item for processing.
        Extracts text, audio, speaker (if specified), and adds constant fields.
        """
        prepared = {
            "text": item[self.config.text_column_name],
            "wave": item[self.config.audio_column_name]["array"],
        }

        # Add speaker column if specified in config
        if self.config.speaker_column_name:
            prepared["speaker"] = item[self.config.speaker_column_name]

        # Add constant fields from config
        constant_cols = self.config.get_constant_columns()
        prepared.update(constant_cols)

        return prepared
