import torch
import multiprocessing as mp
import os
import gzip
import io
import time
from tqdm.auto import tqdm
from utils.nano_codec import NanoCoder
from utils.logging_config import setup_logging

try:
    import orjson
    USE_ORJSON = True
except Exception:
    import json
    USE_ORJSON = False


class AudioWorker:
    """Manages GPU worker processes for audio encoding"""

    SENTINEL = None

    def __init__(self, rank: int, in_q: mp.Queue, out_dir: str, dataset_prefix: str,
                 gzip_level: int, buffer_size: int, lines_per_file: int, num_readers: int,
                 model_id: str):
        self.rank = rank
        self.in_q = in_q
        self.out_dir = out_dir
        self.dataset_prefix = dataset_prefix
        self.gzip_level = gzip_level
        self.buffer_size = buffer_size
        self.lines_per_file = lines_per_file
        self.num_readers = num_readers
        self.model_id = model_id

    def _open_rotated_file(self, idx: int):
        """Opens a new file for writing"""
        path = os.path.join(
            self.out_dir,
            f"{self.dataset_prefix}-worker{self.rank:02d}-{idx:05d}.jsonl.gz"
        )
        raw = open(path, "wb", buffering=0)
        buf = io.BufferedWriter(raw, buffer_size=self.buffer_size)
        gz = gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=self.gzip_level, mtime=0)
        txt = io.TextIOWrapper(gz, encoding="utf-8", newline="\n")
        return path, raw, buf, gz, txt

    def _close_file(self, raw, buf, gz, txt):
        """Safely closes file"""
        for f, name in [(txt, "txt"), (gz, "gz"), (buf, "buf"), (raw, "raw")]:
            try:
                if f:
                    if hasattr(f, 'flush'):
                        f.flush()
                    if hasattr(f, 'detach') and name == "txt":
                        f.detach()
                    elif hasattr(f, 'close'):
                        f.close()
            except Exception:
                pass

    def _dump_line(self, obj, gz, txt):
        """Writes line to file"""
        if USE_ORJSON:
            b = orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NON_STR_KEYS)
            gz.write(b)
            gz.write(b"\n")
        else:
            # Convert numpy to lists for regular json
            for k in ("nano_layer_1", "nano_layer_2", "nano_layer_3", "nano_layer_4"):
                if k in obj and hasattr(obj[k], "tolist"):
                    obj[k] = obj[k].tolist()
            txt.write(json.dumps(obj, ensure_ascii=False))
            txt.write("\n")

    @staticmethod
    def _flatten(x):
        """Converts array to flat form"""
        try:
            import numpy as np
            if x is None:
                return np.array([])
            return x.reshape(-1)
        except Exception:
            return x

    def run(self):
        """Worker process for audio processing"""
        # Setup logging in this worker process to suppress NeMo logs
        setup_logging()

        # Setup tqdm for this worker
        tqdm.set_lock(mp.RLock())

        # GPU emoji for visual appeal
        gpu_emoji = ["🟢", "🔵", "🟣", "🟡", "🔴", "⚫", "⚪", "🟠"][self.rank % 8]

        pbar = tqdm(
            desc=f"{gpu_emoji} GPU-{self.rank}",
            position=self.num_readers + self.rank + 1,
            leave=True,
            unit="items",
            bar_format='{desc}: {n_fmt} | {rate_fmt} | File {postfix}',
            dynamic_ncols=True,
            mininterval=0.5
        )

        torch.set_num_threads(1)

        try:
            # Load model
            pbar.set_description(f"{gpu_emoji} GPU-{self.rank} Loading...")
            model = NanoCoder(self.rank, model_id=self.model_id)
            pbar.set_description(f"{gpu_emoji} GPU-{self.rank} Ready")

            # Initialize file system
            file_idx = 0
            lines_in_file = 0
            path, raw, buf, gz, txt = self._open_rotated_file(file_idx)
            pbar.set_postfix_str(f"{file_idx:05d}")

            n = 0

            # Main processing loop
            while True:
                item = self.in_q.get()
                if item is self.SENTINEL:
                    break

                try:
                    # Process single audio sample
                    codes = model(item["wave"])

                    # Form record for saving
                    rec = {
                        "text": item["text"],
                        "nano_layer_1": self._flatten(codes["nano_layer_1"]),
                        "nano_layer_2": self._flatten(codes["nano_layer_2"]),
                        "nano_layer_3": self._flatten(codes["nano_layer_3"]),
                        "nano_layer_4": self._flatten(codes["nano_layer_4"]),
                        "encoded_len": codes["encoded_len"]
                    }

                    # Add speaker field if present
                    if "speaker" in item:
                        rec["speaker"] = item["speaker"]

                    # Add any additional constant fields
                    for key in item:
                        if key not in ["text", "wave", "speaker"]:
                            rec[key] = item[key]

                    # Write to file
                    self._dump_line(rec, gz, txt)
                    n += 1
                    lines_in_file += 1

                    # Update progress bar
                    pbar.update(1)

                    # File rotation if needed
                    if lines_in_file >= self.lines_per_file:
                        self._close_file(raw, buf, gz, txt)
                        file_idx += 1
                        path, raw, buf, gz, txt = self._open_rotated_file(file_idx)
                        lines_in_file = 0
                        pbar.set_postfix_str(f"{file_idx:05d}")

                except Exception as e:
                    pbar.set_description(f"{gpu_emoji} GPU-{self.rank} ERROR: {str(e)[:30]}")
                    time.sleep(1)
                    pbar.set_description(f"{gpu_emoji} GPU-{self.rank}")
                    continue

        except Exception as e:
            pbar.set_description(f"{gpu_emoji} GPU-{self.rank} CRASHED: {e}")
        finally:
            # Close files
            self._close_file(raw, buf, gz, txt)
            total_files = file_idx + (1 if lines_in_file > 0 else 0)
            pbar.set_description(f"{gpu_emoji} GPU-{self.rank} DONE ({n:,} items, {total_files} files)")
            pbar.close()


def worker_process(rank: int, in_q: mp.Queue, out_dir: str, dataset_prefix: str,
                   gzip_level: int, buffer_size: int, lines_per_file: int, num_readers: int,
                   model_id: str):
    """Entry point for worker process"""
    worker = AudioWorker(rank, in_q, out_dir, dataset_prefix, gzip_level, buffer_size,
                        lines_per_file, num_readers, model_id)
    worker.run()
