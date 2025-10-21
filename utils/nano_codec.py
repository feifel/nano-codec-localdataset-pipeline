import torch
import numpy as np
from nemo.collections.tts.models import AudioCodecModel


class NanoCoder:
    def __init__(self, device_ranc: int, model_id: str = "nvidia/nemo-nano-codec-22khz-0.6kbps-12.5fps"):
        self.nemo_codec_model = AudioCodecModel.from_pretrained(model_id).eval()
        self.device = torch.device(f"cuda:{device_ranc}")
        torch.cuda.set_device(self.device)
        self.nemo_codec_model = self.nemo_codec_model.to(self.device)


    def __call__(self, waveform)->dict:
        audio_tensor = torch.from_numpy(waveform).unsqueeze(dim=0)
        audio_tensor = audio_tensor.to(dtype=torch.float32)
        audio_tensor = audio_tensor.to(self.device)

        audio_len = torch.tensor([audio_tensor[0].shape[0]]).to(self.device)

        with torch.inference_mode():
            encoded_tokens, encoded_len = self.nemo_codec_model.encode(audio=audio_tensor, audio_len=audio_len)

        encoded_tokens = encoded_tokens.squeeze()


        encoded_audio = {   'nano_layer_1' : encoded_tokens[0].to('cpu').numpy(),
                            'nano_layer_2' : encoded_tokens[1].to('cpu').numpy(),
                            'nano_layer_3' : encoded_tokens[2].to('cpu').numpy(),
                            'nano_layer_4' : encoded_tokens[3].to('cpu').numpy(),
                            'encoded_len'  : encoded_len.item()
                        }
        return encoded_audio
