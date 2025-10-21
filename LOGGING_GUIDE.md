# Logging Configuration Guide

## Overview

The pipeline now suppresses all verbose library output (NeMo, PyTorch Lightning, HuggingFace, etc.) and shows **only** the essential pipeline logs.

## What You Will See

### ✅ Visible Logs

1. **Pipeline Status Messages**
   - Configuration validation
   - Dataset loading progress
   - Processing start/completion messages
   - File statistics
   - Final assembly and upload status

2. **tqdm Progress Bars**
   - 📖 Reader workers: Show items read from each dataset shard
   - 🟢🔵🟣🟡 GPU workers: Show items encoded and current file index

3. **Dataset Loading**
   - Dataset name being loaded
   - Number of samples loaded

### ❌ Suppressed Logs

All verbose output from these libraries is hidden:
- NeMo model loading messages
- PyTorch Lightning logs
- HuggingFace datasets progress bars (except our custom messages)
- Transformers library warnings
- File lock messages
- HTTP/download progress bars
- TensorFlow warnings (if imported)

## Example Output

When you run `python main.py`, you'll see something like:

```
🔍 Validating configuration...
✅ Dataset validation passed: All datasets have matching additional columns
✅ Found 2 GPU(s)

📋 Found 2 dataset(s) to process

🔄 Processing dataset 1/2

============================================================
🎯 Processing dataset: nineninesix/audio-ky-elina-elise-dataset
📝 Dataset prefix: audio-ky-elina-elise-dataset
============================================================
📦 Loading dataset: nineninesix/audio-ky-elina-elise-dataset
  ✅ Loaded 15000 samples from nineninesix/audio-ky-elina-elise-dataset

🚀 Starting processing pipeline
💻 CUDA available: True
🔥 GPU workers: 2
📖 Reader workers: 8
📁 Output directory: shards
🗂️  Lines per file: 50,000
📦 Queue size: 100,000
------------------------------------------------------------
📖 Reader-0: 1,250 items | 125.5 items/s | 00:10
📖 Reader-1: 1,187 items | 118.3 items/s | 00:10
...
🟢 GPU-0: 2,435 | 243.5 items/s | File 00000
🔵 GPU-1: 2,401 | 240.1 items/s | File 00000
...

============================================================
🎉 Dataset nineninesix/audio-ky-elina-elise-dataset processed successfully!
📊 Generated 24 files for this dataset, size: 0.45 GB

[Process repeats for dataset 2...]

============================================================
🔨 Assembling final dataset from all shards...
============================================================
📂 Loading shards from: shards/*.jsonl.gz
✅ Final dataset assembled: 30000 samples

💾 Saving dataset locally to: train_dataset
✅ Dataset saved to disk

☁️  Uploading dataset to HuggingFace: nineninesix/pisya
✅ Dataset uploaded to HuggingFace Hub

============================================================
🎊 Pipeline completed successfully!
============================================================

👋 Pipeline finished!
```

## How It Works

The `utils/logging_config.py` module:
1. Suppresses Python warnings
2. Sets all verbose library loggers to ERROR level
3. Sets environment variables to reduce verbosity
4. Disables progress bars from HuggingFace datasets

The logging setup is called at the very start of `main.py` before any other imports, ensuring all libraries are properly silenced.

## Customization

If you need to see more detailed logs for debugging, you can modify `utils/logging_config.py`:

```python
# Change ERROR to WARNING or INFO to see more details
logging.getLogger("nemo").setLevel(logging.WARNING)  # Instead of ERROR
```

Or comment out the `setup_logging()` call in `main.py` to see all logs.
