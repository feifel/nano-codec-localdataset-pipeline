# 🎵 NanoCodec Data Pipeline

[![](https://dcbadge.limes.pink/api/server/https://discord.gg/NzP3rjB4SB?style=flat)](https://discord.gg/NzP3rjB4SB) [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


```
===============================================
          N I N E N I N E S I X  😼
===============================================

          /\_/\
         ( -.- )───┐
          > ^ <    │
===============================================
```
## 🎯 What Does This Do?

This pipeline takes your **audio datasets** from HuggingFace and converts them into **tokenized neural codec representations** using NVIDIA NeMo NanoCodec.

If you're training audio generation models (like TTS, voice cloning, or speech models), you need your audio data in a tokenized format. This pipeline:

- 📦 Downloads audio datasets from HuggingFace
- 🔊 Encodes audio into 4-layer neural codec tokens (super compressed)
- 💾 Saves everything in efficient JSONL.gz format
- ⚡ Uses all your GPUs for maximum speed
- 🚀 Automatically uploads the final dataset back to HuggingFace

**Perfect for:** Anyone training audio models that need tokenized audio data (like language models for speech, TTS systems, voice conversion, etc.)

---

## 🚀 Quick Start

### Prerequisites

- **Linux** (Ubuntu/Debian recommended)
- **At least one NVIDIA GPU** (the more, the faster)
- **Python 3.10+**

### Step 1: Run Setup Script

```bash
sudo ./setup.sh
```

The script will:
- Check your Python version
- Install system dependencies
- Create a virtual environment
- Install all Python packages

Setup takes ~5 minutes.

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` appear in your terminal prompt.

### Step 3: Login to HuggingFace

You need to authenticate so the pipeline can download and upload datasets:

```bash
# Store credentials (so you don't have to log in every time)
git config --global credential.helper store

# Login to HuggingFace
hf auth login
```

Paste your HuggingFace token when prompted. Get one here: https://huggingface.co/settings/tokens

### Step 4: Configure Your Pipeline

Edit `config.yaml` to tell the pipeline what to process:

```bash
nano config.yaml
```

See the **Configuration Guide** below for details!

### Step 5: Run the Pipeline

```bash
python main.py
```

You'll see progress bars for each GPU and reader process.

---

## 📝 Configuration Guide

The `config.yaml` file controls everything. Here's what each part does:

### Example Configuration

```yaml
base_settings:
  audio_codec: nvidia/nemo-nano-codec-22khz-0.6kbps-12.5fps  # The model to use
  num_readers: 8              # How many CPU processes read data (more = faster)
  qsize: 100000               # Queue size (bigger = more RAM, but smoother)
  OUT_DIR: shards             # Where to save the encoded files
  gzip_level: 1               # Compression (1=fast, 9=small files)
  buffer_size: 16777216       # Write buffer (16MB is good)
  lines_per_file: 50000       # Split output into chunks of 50k samples
  load_dataset_num_proc: 20   # Parallel processes for loading (faster!)

save_settings:
  local: train_dataset                    # Save to this folder (or null to skip)
  hf_upload: your-username/your-dataset   # Upload to HF (or null to skip)

hf_datasets:
  - name: your-username/audio-dataset-1   # HuggingFace dataset to process
    sub_name: null                        # Dataset subset/config (or null)
    split: train                          # Which split to use (train/test/validation)
    text_column_name: text                # Name of the text column
    audio_column_name: audio              # Name of the audio column
    speaker_column_name: null             # Speaker column (or null if none)
    add_constant:                         # Add these fields to every sample
      - key: speaker
        value: speaker1
      - key: lang
        value: en

  - name: your-username/audio-dataset-2   # You can add multiple datasets!
    sub_name: clean                       # Example: LibriSpeech has 'clean', 'other' subsets
    split: train                          # Which split to use
    text_column_name: sentences
    audio_column_name: audio
    speaker_column_name: speaker_id       # This dataset has speaker info
    add_constant:
      - key: lang
        value: en
```

### 🔧 What Each Setting Does

#### `base_settings` - Core Configuration

| Setting | What It Does | Recommended Value |
|---------|--------------|-------------------|
| `audio_codec` | Which NeMo model to use | `nvidia/nemo-nano-codec-22khz-0.6kbps-12.5fps` |
| `num_readers` | CPU processes reading data | 8 (more if you have many CPU cores) |
| `qsize` | Queue buffer size | 100000 (increase if you have lots of RAM) |
| `OUT_DIR` | Output folder | `shards` |
| `gzip_level` | Compression level | 1 (fast) or 9 (small files) |
| `buffer_size` | Write buffer size | 16777216 (16MB) |
| `lines_per_file` | Samples per output file | 50000 |
| `load_dataset_num_proc` | Parallel loading | 20 (more = faster loading) |

#### `save_settings` - Where to Save

| Setting | What It Does | Example |
|---------|--------------|---------|
| `local` | Save to local disk | `train_dataset` or `null` to skip |
| `hf_upload` | Upload to HuggingFace | `username/dataset-name` or `null` to skip |

#### `hf_datasets` - Your Datasets

Each dataset entry has:

| Field | What It Does | Example |
|-------|--------------|---------|
| `name` | HuggingFace dataset name | `openslr/librispeech_asr` |
| `sub_name` | Dataset subset/configuration | `clean`, `other`, or `null` if none |
| `split` | Which split to load | `train`, `test`, `validation` |
| `text_column_name` | Column with text/transcription | `text`, `sentence`, `transcription` |
| `audio_column_name` | Column with audio data | `audio`, `speech`, `wav` |
| `speaker_column_name` | Column with speaker ID | `speaker`, `speaker_id`, or `null` |
| `add_constant` | Fields to add to every sample | Add metadata like language, speaker, etc. |

**💡 Pro Tip:** The `add_constant` fields are super useful! Add metadata like:
- Language (`lang: en`)
- Dataset source (`source: librispeech`)
- Speaker info if not in dataset (`speaker: john`)

---

## 📊 What You Get

After processing, you'll have:

### Output Files

Files in `shards/` folder (or your `OUT_DIR`):
```
dataset-name-worker00-00000.jsonl.gz
dataset-name-worker00-00001.jsonl.gz
dataset-name-worker01-00000.jsonl.gz
...
```

### Final Dataset

If you set `local` or `hf_upload`, you'll get a merged dataset with:

```json
{
  "text": "Hello world",
  "nano_layer_1": [123, 456, 789, ...],  // Codec tokens layer 1
  "nano_layer_2": [234, 567, 890, ...],  // Codec tokens layer 2
  "nano_layer_3": [345, 678, 901, ...],  // Codec tokens layer 3
  "nano_layer_4": [456, 789, 012, ...],  // Codec tokens layer 4
  "encoded_len": 150,                    // Number of tokens
  "speaker": "speaker1",                 // Your metadata
  "lang": "en"
}
```

**Perfect for:** Training TTS models, voice conversion, speech generation, etc.

---

## 🎓 For Model Trainers

### Why Use This Pipeline?

If you're training audio generation models, you need your audio in a **tokenized** format. This pipeline:

1. **Converts raw audio → tokens** using state-of-the-art neural codecs
2. **Compresses 22kHz audio** down to just **0.6 kbps** (12.5 tokens/second!)
3. **Preserves quality** through hierarchical 4-layer encoding
4. **Handles large datasets** with automatic sharding and compression

### What Models Need This?

- **Text-to-Speech (TTS)** models
- **Voice cloning** systems
- **Voice conversion** models

### How to Use the Output

```python
from datasets import load_dataset

# Load your processed dataset
dataset = load_dataset("your-username/your-dataset")

# Each sample has:
# - text: the transcription
# - nano_layer_1-4: codec tokens (4 layers)
# - encoded_len: sequence length
# - any metadata you added (speaker, lang, etc.)

for sample in dataset:
    text = sample['text']
    tokens_layer1 = sample['nano_layer_1']  # Shape: [encoded_len]
    tokens_layer2 = sample['nano_layer_2']
    # Use these tokens to train your model!
```

### Understanding the Codec

- **4 layers** = hierarchical encoding (coarse → fine details)
- **12.5 fps** = 12.5 tokens per second of audio
- **22kHz** = input audio sample rate
- **0.6 kbps** = extremely compressed!

---

## 🔧 Advanced Options

### Processing Multiple Datasets

Just add more entries to `hf_datasets`:

```yaml
hf_datasets:
  - name: dataset1
    # ... config ...
  - name: dataset2
    # ... config ...
  - name: dataset3
    # ... config ...
```

All datasets will be processed sequentially and merged into one final dataset.

### Adding Metadata

Use `add_constant` to tag your data:

```yaml
add_constant:
  - key: dataset_source
    value: librispeech
  - key: lang
    value: en
  - key: quality
    value: clean
```

This helps when training multi-dataset models!

### GPU Utilization

The pipeline automatically uses **all available GPUs**. Each GPU:
- Gets its own worker process
- Processes samples from a shared queue
- Writes to separate shard files

More GPUs = faster processing! 🚀

---

## 📖 Documentation

- **`LOGGING_GUIDE.md`** - Logging configuration
- **`config.yaml`** - Your configuration file (edit this!)

---

## ❓ Troubleshooting

### "No CUDA devices found"

Make sure you have:
1. NVIDIA GPU installed
2. NVIDIA drivers installed
3. CUDA toolkit installed

Check with: `nvidia-smi`

### "Permission denied" on setup.sh

Run: `chmod +x setup.sh`

### HuggingFace login fails

Get a token from: https://huggingface.co/settings/tokens

> Make sure you select "Write" permissions

### Pipeline runs slowly

- Increase `num_readers` (more CPU processes)
- Increase `load_dataset_num_proc` (faster loading)
- Check GPU utilization with `nvidia-smi`

### Out of memory

- Decrease `qsize` (smaller queue)
- Decrease `num_readers` (fewer parallel processes)
- Process smaller datasets

---

## 💬 Need Help?

- 📚 Check the documentation files
- 🐛 Found a bug? Open an issue
- [![](https://dcbadge.limes.pink/api/server/https://discord.gg/NzP3rjB4SB?style=flat)](https://discord.gg/NzP3rjB4SB)
---

## 📜 License

Apache 2. See `LICENSE` file for details.
