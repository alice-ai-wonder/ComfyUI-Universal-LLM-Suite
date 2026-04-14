# =============================================================================
# Universal LLM Suite - Gemini Nodes
# =============================================================================

import traceback
import asyncio
import torch
import numpy as np
from .nodes_base import (
    audio_dict_to_wav_bytes,
    wav_bytes_to_audio_dict,
    pcm_bytes_to_audio_dict,
    empty_audio,
    image_tensor_to_png_bytes,
)

CATEGORY = "✨ Universal LLM"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VOICE_NAMES = [
    "Puck",    # Warm, friendly male
    "Charon",  # Deep, resonant male
    "Kore",    # Calm, clear female
    "Fenrir",  # Energetic female
    "Aoede",   # Default, expressive female
]

GEMINI_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemma-3-27b-it",
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-3.1-flash-live-preview",
]

# Models that support bidirectional audio via the Live API
LIVE_API_MODELS = {
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-3.1-flash-live-preview",
}

# Models that do NOT support system_instruction (Gemma family)
GEMMA_MODELS = {
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemma-3-27b-it",
}

# Models that do NOT support image (vision) input
IMAGE_UNSUPPORTED_MODELS = {
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-3.1-flash-live-preview",
}

# ---------------------------------------------------------------------------
# Helper: lazy import google-genai
# ---------------------------------------------------------------------------

def _get_genai():
    try:
        from google import genai
        return genai
    except ImportError:
        raise ImportError(
            "❌ google-genai SDK is not installed.\n"
            "   Run:  pip install google-genai\n"
            "   inside your ComfyUI Python environment."
        )

def _get_genai_types():
    try:
        from google.genai import types
        return types
    except ImportError:
        raise ImportError(
            "❌ google-genai SDK is not installed.\n"
            "   Run:  pip install google-genai\n"
            "   inside your ComfyUI Python environment."
        )


# =============================================================================
# Node: Gemini Model Configurator
# =============================================================================

class GeminiModelConfigurator:
    """Setup API key and select a Gemini model."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "default": "",
                    "placeholder": "Enter your Gemini API key",
                }),
                "model_name": (GEMINI_MODELS, {
                    "default": "gemini-2.5-flash",
                }),
                "voice_name": (VOICE_NAMES, {
                    "default": "Aoede",
                }),
                "thinking_level": (["default", "minimal", "low", "medium", "high"], {
                    "default": "default",
                }),
            },
        }

    RETURN_TYPES = ("GEMINI_MODEL",)
    RETURN_NAMES = ("gemini_model",)
    FUNCTION = "configure"
    CATEGORY = CATEGORY
    DESCRIPTION = "Configure the Gemini API key, select a model, and set thinking level."

    def configure(self, api_key: str, model_name: str, voice_name: str = "Aoede", thinking_level: str = "default"):
        if not api_key or not api_key.strip():
            raise ValueError("❌ API key must not be empty.")

        genai = _get_genai()
        client = genai.Client(api_key=api_key.strip())

        payload = {
            "client": client,
            "model_name": model_name,
            "api_key": api_key.strip(),
            "is_live": model_name in LIVE_API_MODELS,
            "voice_name": voice_name,
            "thinking_level": thinking_level,
        }
        print(f"✅ [Universal LLM Suite] Configured Gemini model: {model_name} (Voice: {voice_name}, Thinking: {thinking_level})")
        return (payload,)


# =============================================================================
# Node: Gemini API Runner
# =============================================================================

class GeminiAPIRunner:
    """Core engine – sends text (and optional audio) to Gemini and returns
    both text and audio responses."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "gemini_model": ("GEMINI_MODEL",),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "forceInput": True,
                }),
                "user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "forceInput": True,
                }),
            },
            "optional": {
                "image_input": ("IMAGE",),
                "audio_input": ("AUDIO",),
            },
        }

    RETURN_TYPES = ("STRING", "AUDIO", "STRING",)
    RETURN_NAMES = ("response_text", "response_audio", "response_thoughts",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = "Send prompts to the Gemini API and receive text, audio, & thoughts."

    def _run_standard(self, gemini_model, client, model_name, system_prompt, user_prompt, audio_input, image_input):
        types = _get_genai_types()
        contents = []

        if image_input is not None:
            if model_name in IMAGE_UNSUPPORTED_MODELS:
                raise ValueError(
                    f"❌ Model '{model_name}' does not support image input.\n"
                    f"   Image-compatible models: "
                    + ", ".join(m for m in GEMINI_MODELS if m not in IMAGE_UNSUPPORTED_MODELS)
                )
            png_bytes = image_tensor_to_png_bytes(image_input)
            image_part = types.Part.from_bytes(data=png_bytes, mime_type="image/png")
            contents.append(image_part)

        if audio_input is not None:
            wav_bytes = audio_dict_to_wav_bytes(audio_input)
            audio_part = types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")
            contents.append(audio_part)

        is_gemma = model_name in GEMMA_MODELS
        combined_prompt = user_prompt
        if is_gemma and system_prompt.strip():
            combined_prompt = f"[System Instruction]\n{system_prompt.strip()}\n\n[User]\n{user_prompt}"

        if combined_prompt.strip():
            contents.append(combined_prompt)

        modalities = ["TEXT"]
        if "gemini-3" in model_name or "audio" in model_name or "tts" in model_name:
            modalities = ["AUDIO", "TEXT"]
        
        speech_config = None
        if "AUDIO" in modalities:
            speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=gemini_model.get("voice_name", "Aoede")
                    )
                )
            )

        thinking_level = gemini_model.get("thinking_level", "default")
        thinking_config = None
        if thinking_level != "default":
            try:
                thinking_config = types.ThinkingConfig(include_thoughts=True, thinking_level=thinking_level)
            except Exception:
                thinking_config = {"include_thoughts": True, "thinking_level": thinking_level}

        config = types.GenerateContentConfig(
            system_instruction=system_prompt if (system_prompt.strip() and not is_gemma) else None,
            response_modalities=modalities,
            speech_config=speech_config,
            thinking_config=thinking_config,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        # Manually extract text and thoughts to avoid pollution
        response_text = ""
        response_thoughts = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text:
                    if getattr(part, 'thought', False):
                        response_thoughts += part.text
                    else:
                        response_text += part.text
        
        # Fallback if manual extraction missed something or structure was different
        if not response_text and hasattr(response, "text") and response.text:
            response_text = response.text
            # If we used the fallback, we might have thoughts in the text, 
            # but it's better than no text at all.

        response_audio = None
        if hasattr(response, "parts") and response.parts:
             for part in response.parts:
                 if hasattr(part, "inline_data") and part.inline_data:
                     # ... existing audio extraction logic stays the same ...
                     mime = part.inline_data.mime_type
                     data = part.inline_data.data
                     if mime and mime.startswith("audio/"):
                         if mime == "audio/pcm" or mime == "audio/pcm;rate=16000" or mime == "audio/pcm;rate=24000":
                             sample_rate = 24000
                             if "16000" in mime: sample_rate = 16000
                             response_audio = pcm_bytes_to_audio_dict(data, sample_rate=sample_rate)
                         else:
                             response_audio = wav_bytes_to_audio_dict(data)
                         break
                         
        if response_audio is None:
            response_audio = empty_audio()
            
        return response_text, response_thoughts, response_audio

    def _run_live(self, gemini_model, client, model_name, system_prompt, user_prompt, audio_input):
        types = _get_genai_types()

        async def _live_session():
            speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=gemini_model.get("voice_name", "Aoede")
                    )
                )
            )

            thinking_level = gemini_model.get("thinking_level", "default")
            thinking_config = None
            if thinking_level != "default":
                try:
                    thinking_config = types.ThinkingConfig(include_thoughts=True, thinking_level=thinking_level)
                except Exception:
                    thinking_config = {"include_thoughts": True, "thinking_level": thinking_level}

            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config,
                thinking_config=thinking_config,
                system_instruction=types.Content(
                    parts=[types.Part(text=system_prompt)]
                ) if system_prompt.strip() else None,
            )

            all_audio_bytes = b""
            all_text = ""
            all_thoughts = ""

            async with client.aio.live.connect(model=model_name, config=config) as session:
                pcm_16k = None
                if audio_input is not None:
                    waveform = audio_input["waveform"]
                    src_sr = audio_input["sample_rate"]

                    if isinstance(waveform, torch.Tensor):
                        wav_np = waveform.squeeze().cpu().numpy()
                    else:
                        wav_np = np.array(waveform).squeeze()

                    if wav_np.ndim > 1:
                        wav_np = wav_np.mean(axis=0)

                    target_sr = 16000
                    if src_sr != target_sr:
                        import librosa
                        wav_np = librosa.resample(wav_np.astype(np.float32), orig_sr=src_sr, target_sr=target_sr)

                    wav_np = np.clip(wav_np, -1.0, 1.0)
                    pcm_16k = (wav_np * 32767).astype(np.int16).tobytes()

                if pcm_16k:
                    await session.send_realtime_input(
                        audio=types.Blob(data=pcm_16k, mime_type="audio/pcm;rate=16000"),
                    )

                text_to_send = user_prompt.strip()
                if text_to_send:
                    await session.send_realtime_input(text=text_to_send)
                elif not pcm_16k:
                    await session.send_realtime_input(text="Hello.")

                silence_samples = 16000 * 3
                silence_pcm = bytes(silence_samples * 2)
                await session.send_realtime_input(
                    audio=types.Blob(data=silence_pcm, mime_type="audio/pcm;rate=16000"),
                )

                async for response in session.receive():
                    if response.server_content:
                        sc = response.server_content
                        if sc.model_turn and sc.model_turn.parts:
                            for part in sc.model_turn.parts:
                                if part.text:
                                    if getattr(part, 'thought', False):
                                        all_thoughts += part.text
                                    else:
                                        all_text += part.text
                                if part.inline_data and part.inline_data.data:
                                    all_audio_bytes += part.inline_data.data
                        if hasattr(sc, 'output_transcription') and sc.output_transcription:
                            if hasattr(sc.output_transcription, 'text') and sc.output_transcription.text:
                                # This is user speech transcription, let's keep it clean or ignore
                                pass
                        if sc.turn_complete:
                            break

            return all_text, all_thoughts, all_audio_bytes

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    text, thoughts, audio_bytes = pool.submit(
                        lambda: asyncio.run(_live_session())
                    ).result()
            else:
                text, thoughts, audio_bytes = loop.run_until_complete(_live_session())
        except RuntimeError:
            text, thoughts, audio_bytes = asyncio.run(_live_session())

        if audio_bytes and len(audio_bytes) > 0:
            audio_dict = pcm_bytes_to_audio_dict(audio_bytes, sample_rate=24000)
        else:
            audio_dict = empty_audio()

        return text, thoughts, audio_dict

    def run(self, gemini_model: dict, system_prompt: str, user_prompt: str,
            image_input=None, audio_input=None):

        client = gemini_model["client"]
        model_name = gemini_model["model_name"]
        is_live = gemini_model.get("is_live", False)

        print(f"🚀 [Universal LLM Suite] Running Gemini model={model_name}, live={is_live}")

        try:
            if is_live:
                if image_input is not None:
                    raise ValueError(
                        f"❌ Model '{model_name}' (Live API) does not support image input.\n"
                        f"   Use a standard model for image analysis."
                    )
                resp_text, resp_thoughts, resp_audio = self._run_live(gemini_model, client, model_name, system_prompt, user_prompt, audio_input)
            else:
                resp_text, resp_thoughts, resp_audio = self._run_standard(gemini_model, client, model_name, system_prompt, user_prompt, audio_input, image_input)
        except Exception as e:
            traceback.print_exc()
            resp_text = f"❌ Gemini API Error: {e}"
            resp_thoughts = ""
            resp_audio = empty_audio()

        return (resp_text, resp_audio, resp_thoughts,)
