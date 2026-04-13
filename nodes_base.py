# =============================================================================
# Universal LLM Suite - Shared Base Nodes & Helpers
# =============================================================================

import os
import io
import struct
import numpy as np
import torch
import folder_paths
from datetime import datetime

CATEGORY = "✨ Universal LLM"

# ---------------------------------------------------------------------------
# Helper: WAV encoding / decoding (Shared by both Gemini and OpenAI)
# ---------------------------------------------------------------------------

def _pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Convert raw PCM bytes to a WAV file in memory."""
    buf = io.BytesIO()
    num_samples = len(pcm_data) // sample_width
    data_size = num_samples * channels * sample_width
    # WAV header
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + data_size))
    buf.write(b'WAVE')
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16))  # PCM header size
    buf.write(struct.pack('<H', 1))   # PCM format
    buf.write(struct.pack('<H', channels))
    buf.write(struct.pack('<I', sample_rate))
    buf.write(struct.pack('<I', sample_rate * channels * sample_width))
    buf.write(struct.pack('<H', channels * sample_width))
    buf.write(struct.pack('<H', sample_width * 8))
    buf.write(b'data')
    buf.write(struct.pack('<I', data_size))
    buf.write(pcm_data)
    return buf.getvalue()


def audio_dict_to_wav_bytes(audio_dict: dict) -> bytes:
    """Convert ComfyUI AUDIO dict (waveform tensor + sample_rate) to WAV bytes."""
    waveform = audio_dict["waveform"]  # [batch, channels, samples]
    sr = audio_dict["sample_rate"]

    if isinstance(waveform, torch.Tensor):
        wav_np = waveform.squeeze().cpu().numpy()
    else:
        wav_np = np.array(waveform).squeeze()

    # Mono
    if wav_np.ndim > 1:
        wav_np = wav_np.mean(axis=0)

    # Normalise to int16
    wav_np = np.clip(wav_np, -1.0, 1.0)
    pcm = (wav_np * 32767).astype(np.int16).tobytes()

    return _pcm_to_wav_bytes(pcm, sample_rate=sr)


def wav_bytes_to_audio_dict(wav_bytes: bytes) -> dict:
    """Convert WAV bytes to ComfyUI AUDIO dict."""
    buf = io.BytesIO(wav_bytes)

    # Parse WAV header
    buf.read(4)  # RIFF
    buf.read(4)  # file size
    buf.read(4)  # WAVE

    sr = 24000
    channels = 1
    sample_width = 2

    while True:
        chunk_id = buf.read(4)
        if len(chunk_id) < 4:
            break
        chunk_size = struct.unpack('<I', buf.read(4))[0]
        if chunk_id == b'fmt ':
            fmt_data = buf.read(chunk_size)
            channels = struct.unpack('<H', fmt_data[2:4])[0]
            sr = struct.unpack('<I', fmt_data[4:8])[0]
            sample_width = struct.unpack('<H', fmt_data[14:16])[0] // 8
        elif chunk_id == b'data':
            pcm_data = buf.read(chunk_size)
            break
        else:
            buf.read(chunk_size)

    samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32767.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)

    waveform = torch.from_numpy(samples).unsqueeze(0).unsqueeze(0)  # [1,1,S]
    return {"waveform": waveform, "sample_rate": sr}


def pcm_bytes_to_audio_dict(pcm_data: bytes, sample_rate: int = 24000) -> dict:
    """Convert raw PCM (int16 LE) to ComfyUI AUDIO dict."""
    samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32767.0
    waveform = torch.from_numpy(samples).unsqueeze(0).unsqueeze(0)
    return {"waveform": waveform, "sample_rate": sample_rate}


def empty_audio():
    """Return a silent, minimal AUDIO dict."""
    return {"waveform": torch.zeros(1, 1, 1), "sample_rate": 24000}


def image_tensor_to_png_bytes(image_tensor) -> bytes:
    """Convert ComfyUI IMAGE tensor [B,H,W,C] (float 0-1) to PNG bytes."""
    if isinstance(image_tensor, torch.Tensor):
        img_np = image_tensor[0].cpu().numpy()  # Take first image in batch
    else:
        img_np = np.array(image_tensor)
        if img_np.ndim == 4:
            img_np = img_np[0]

    # Convert float 0-1 to uint8 0-255
    img_np = np.clip(img_np * 255.0, 0, 255).astype(np.uint8)

    # Encode as PNG
    from PIL import Image
    img = Image.fromarray(img_np)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def image_tensor_to_base64_png(image_tensor) -> str:
    """Convert ComfyUI IMAGE tensor to base64 string for OpenAI."""
    import base64
    png_bytes = image_tensor_to_png_bytes(image_tensor)
    return base64.b64encode(png_bytes).decode('utf-8')


# =============================================================================
# Node: LLM Dual Prompt
# =============================================================================

class LLMDualPrompt:
    """Construct system + user prompts."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful AI assistant.",
                    "placeholder": "System prompt: define the AI's role, constraints, etc.",
                }),
                "user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "User prompt: your actual instruction or question.",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("system_prompt", "user_prompt",)
    FUNCTION = "build"
    CATEGORY = CATEGORY
    DESCRIPTION = "Build system and user prompts for LLMs."

    def build(self, system_prompt: str, user_prompt: str):
        return (system_prompt, user_prompt,)


# =============================================================================
# Node: LLM Text Display
# =============================================================================

class LLMTextDisplay:
    """Display text output on the node UI (via JS widget)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "display"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    DESCRIPTION = "Display the LLM response text on the node."

    def display(self, text: str):
        return {"ui": {"text": [text]}}


# =============================================================================
# Node: LLM Audio Save & Play
# =============================================================================

class LLMAudioSavePlay:
    """Save audio to output folder and allow playback via JS widget."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_and_play"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    DESCRIPTION = "Save generated audio as WAV and play it in the browser."

    def save_and_play(self, audio: dict):
        waveform = audio["waveform"]
        sr = audio["sample_rate"]

        # Check for empty / silence-only audio
        if isinstance(waveform, torch.Tensor):
            if waveform.numel() <= 1:
                print("⚠️ [Universal LLM Suite] No audio data to save.")
                return {"ui": {"audio_path": [""], "audio_filename": [""]}}

        wav_bytes = audio_dict_to_wav_bytes(audio)

        # Save to output directory
        output_dir = folder_paths.get_output_directory()
        llm_dir = os.path.join(output_dir, "llm_audio")
        os.makedirs(llm_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"llm_audio_{timestamp}.wav"
        filepath = os.path.join(llm_dir, filename)

        with open(filepath, "wb") as f:
            f.write(wav_bytes)

        print(f"💾 [Universal LLM Suite] Saved audio: {filepath}")

        # Also save to temp for browser playback
        temp_dir = folder_paths.get_temp_directory()
        temp_sub = "llm_suite_audio"
        full_temp = os.path.join(temp_dir, temp_sub)
        os.makedirs(full_temp, exist_ok=True)

        temp_filename = f"play_{timestamp}.wav"
        temp_path = os.path.join(full_temp, temp_filename)
        with open(temp_path, "wb") as f:
            f.write(wav_bytes)

        return {
            "ui": {
                "audio_path": [f"/view?filename={temp_filename}&subfolder={temp_sub}&type=temp"],
                "audio_filename": [filename],
            }
        }
