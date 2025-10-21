import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class DatasetConfig:
    """Configuration for a single dataset"""
    name: str
    text_column_name: str
    audio_column_name: str
    speaker_column_name: Optional[str]
    add_constant: Optional[List[Dict[str, str]]]
    split: str = "train"  # Default to 'train' split
    sub_name: Optional[str] = None  # Dataset subset/configuration name

    @property
    def dataset_prefix(self) -> str:
        """Extract dataset prefix from name (part after /)"""
        return self.name.split('/')[-1]

    def get_constant_columns(self) -> Dict[str, str]:
        """Get constant columns as a dictionary"""
        if not self.add_constant:
            return {}
        return {item['key']: item['value'] for item in self.add_constant}


@dataclass
class BaseSettings:
    """Base pipeline settings"""
    audio_codec: str
    num_readers: int
    qsize: int
    OUT_DIR: str
    gzip_level: int
    buffer_size: int
    lines_per_file: int
    load_dataset_num_proc: int = 5  # Default to 5 if not specified


@dataclass
class SaveSettings:
    """Settings for saving/uploading datasets"""
    local: Optional[str]
    hf_upload: Optional[str]


class ConfigManager:
    """Manages configuration loading and validation"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.base_settings = BaseSettings(**self.config['base_settings'])
        self.save_settings = SaveSettings(**self.config['save_settings'])
        self.datasets = [DatasetConfig(**ds) for ds in self.config['hf_datasets']]

    def validate_datasets(self) -> None:
        """
        Validate that all datasets have matching additional columns.
        This prevents conflicts when merging the final dataset.
        """
        if not self.datasets:
            raise ValueError("No datasets specified in configuration")

        # Get all constant column keys from all datasets
        all_constant_keys = set()
        dataset_constant_keys = []

        for ds in self.datasets:
            constant_keys = set(ds.get_constant_columns().keys())
            dataset_constant_keys.append((ds.name, constant_keys))
            all_constant_keys.update(constant_keys)

        # Check if all datasets have the same constant columns
        if all_constant_keys:
            for ds_name, keys in dataset_constant_keys:
                missing_keys = all_constant_keys - keys
                if missing_keys:
                    raise ValueError(
                        f"Dataset '{ds_name}' is missing constant columns: {missing_keys}. "
                        f"All datasets must have the same constant columns for proper merging."
                    )

        print("✅ Dataset validation passed: All datasets have matching additional columns")

    def get_datasets(self) -> List[DatasetConfig]:
        """Get list of dataset configurations"""
        return self.datasets

    def get_base_settings(self) -> BaseSettings:
        """Get base pipeline settings"""
        return self.base_settings

    def get_save_settings(self) -> SaveSettings:
        """Get save/upload settings"""
        return self.save_settings
