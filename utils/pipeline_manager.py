import torch
import multiprocessing as mp
import os
from datasets import load_dataset, concatenate_datasets
from typing import List
from utils.config_manager import ConfigManager, DatasetConfig
from utils.dataset_processor import DatasetProcessor
from utils.audio_worker import worker_process, AudioWorker
from utils.reader_worker import reader_worker_process


class PipelineManager:
    """Manages the entire audio processing pipeline"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.base_settings = self.config_manager.get_base_settings()
        self.save_settings = self.config_manager.get_save_settings()
        self.num_gpus = torch.cuda.device_count()

        # Ensure output directory exists
        os.makedirs(self.base_settings.OUT_DIR, exist_ok=True)

    def validate(self):
        """Validate configuration and environment"""
        print("🔍 Validating configuration...")
        self.config_manager.validate_datasets()

        if self.num_gpus == 0:
            raise RuntimeError("❌ ERROR: No CUDA devices found!")

        print(f"✅ Found {self.num_gpus} GPU(s)")

    def process_single_dataset(self, dataset_config: DatasetConfig):
        """Process a single dataset through the pipeline"""
        print(f"\n{'='*60}")
        print(f"🎯 Processing dataset: {dataset_config.name}")
        print(f"📝 Dataset prefix: {dataset_config.dataset_prefix}")
        print(f"{'='*60}")

        # Load dataset
        processor = DatasetProcessor(dataset_config)
        processor.load_dataset(num_proc=self.base_settings.load_dataset_num_proc)

        # Setup multiprocessing
        mp.set_start_method("spawn", force=True)
        q = mp.Queue(maxsize=self.base_settings.qsize)

        print(f"\n🚀 Starting processing pipeline")
        print(f"💻 CUDA available: {torch.cuda.is_available()}")
        print(f"🔥 GPU workers: {self.num_gpus}")
        print(f"📖 Reader workers: {self.base_settings.num_readers}")
        print(f"⚙️  Dataset load processes: {self.base_settings.load_dataset_num_proc}")
        print(f"📁 Output directory: {self.base_settings.OUT_DIR}")
        print(f"🗂️  Lines per file: {self.base_settings.lines_per_file:,}")
        print(f"📦 Queue size: {self.base_settings.qsize}")
        print("-" * 60)

        # Start GPU worker processes
        workers = [
            mp.Process(
                target=worker_process,
                args=(
                    i,
                    q,
                    self.base_settings.OUT_DIR,
                    dataset_config.dataset_prefix,
                    self.base_settings.gzip_level,
                    self.base_settings.buffer_size,
                    self.base_settings.lines_per_file,
                    self.base_settings.num_readers,
                    self.base_settings.audio_codec  # Pass model_id from config
                )
            )
            for i in range(self.num_gpus)
        ]

        for p in workers:
            p.start()

        # Shard the dataset for readers
        dataset = processor.get_dataset()
        sharded_datasets = [
            dataset.shard(num_shards=self.base_settings.num_readers, index=i)
            for i in range(self.base_settings.num_readers)
        ]

        # Create dataset processors for each shard (they share the config but have different shards)
        shard_processors = []
        for i in range(self.base_settings.num_readers):
            shard_proc = DatasetProcessor(dataset_config)
            shard_proc.dataset = sharded_datasets[i]
            shard_processors.append(shard_proc)

        # Start reader processes
        readers = [
            mp.Process(
                target=reader_worker_process,
                args=(i, self.base_settings.num_readers, shard_processors[i], q)
            )
            for i in range(self.base_settings.num_readers)
        ]

        for pr in readers:
            pr.start()

        try:
            # Wait for all readers to complete
            for pr in readers:
                pr.join()

            # Send SENTINEL to all workers after all readers are done
            for i in range(self.num_gpus):
                q.put(AudioWorker.SENTINEL)

            # Wait for workers to complete
            for p in workers:
                p.join()

            print("\n" + "=" * 60)
            print(f"🎉 Dataset {dataset_config.name} processed successfully!")

            # Show file statistics
            if os.path.exists(self.base_settings.OUT_DIR):
                files = [f for f in os.listdir(self.base_settings.OUT_DIR)
                        if f.startswith(dataset_config.dataset_prefix)]
                if files:
                    total_size = sum(
                        os.path.getsize(os.path.join(self.base_settings.OUT_DIR, f))
                        for f in files
                    )
                    print(f"📊 Generated {len(files)} files for this dataset, "
                          f"size: {total_size / 1024**3:.2f} GB")

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted! Terminating processes...")

            # Stop progress bars
            for pr in readers:
                pr.terminate()
            for p in workers:
                p.terminate()

            # Wait for completion with timeout
            for pr in readers:
                pr.join(timeout=10)
            for p in workers:
                p.join(timeout=10)

            print("🛑 All processes terminated")
            raise

    def assemble_and_save_final_dataset(self):
        """Assemble all processed shards into final dataset and save/upload"""
        print(f"\n{'='*60}")
        print("🔨 Assembling final dataset from all shards...")
        print(f"{'='*60}")

        # Load all JSONL.gz files from output directory
        shard_files = os.path.join(self.base_settings.OUT_DIR, "*.jsonl.gz")
        print(f"📂 Loading shards from: {shard_files}")

        final_dataset = load_dataset(
            "json",
            data_dir=self.base_settings.OUT_DIR,
            data_files="*.jsonl.gz",
            split='train',
            verification_mode='no_checks'
        )

        print(f"✅ Final dataset assembled: {len(final_dataset)} samples")

        # Save locally if specified
        if self.save_settings.local:
            print(f"\n💾 Saving dataset locally to: {self.save_settings.local}")
            final_dataset.save_to_disk(self.save_settings.local)
            print(f"✅ Dataset saved to disk")

        # Upload to HuggingFace if specified
        if self.save_settings.hf_upload:
            print(f"\n☁️  Uploading dataset to HuggingFace: {self.save_settings.hf_upload}")
            final_dataset.push_to_hub(self.save_settings.hf_upload, private=True)
            print(f"✅ Dataset uploaded to HuggingFace Hub")

        print(f"\n{'='*60}")
        print("🎊 Pipeline completed successfully!")
        print(f"{'='*60}")

    def run(self):
        """Run the complete pipeline for all datasets"""
        # Validate configuration
        self.validate()

        # Get all datasets to process
        datasets = self.config_manager.get_datasets()
        print(f"\n📋 Found {len(datasets)} dataset(s) to process")

        # Process each dataset sequentially
        for idx, dataset_config in enumerate(datasets, 1):
            print(f"\n🔄 Processing dataset {idx}/{len(datasets)}")
            self.process_single_dataset(dataset_config)

        # After all datasets are processed, assemble and save
        self.assemble_and_save_final_dataset()

        print("\n👋 Pipeline finished!")
