# =============================================================================
# Universal LLM Suite - OpenAI Nodes
# =============================================================================

import traceback
from .nodes_base import (
    image_tensor_to_base64_png,
    pcm_bytes_to_audio_dict,
    empty_audio,
)

CATEGORY = "✨ Universal LLM"

OPENAI_MODELS = [
    "gpt-5.4-mini",
    "gpt-5.4-nano",
    "gpt-4o-mini",
    "o1-mini",
    "gpt-5.4",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

OPENAI_VOICES = [
    "alloy",
    "echo",
    "fable",
    "onyx",
    "nova",
    "shimmer",
]

def _get_openai():
    try:
        import openai
        return openai
    except ImportError:
        raise ImportError(
            "❌ openai SDK is not installed.\n"
            "   Run:  pip install openai\n"
            "   inside your ComfyUI Python environment."
        )

# =============================================================================
# Node: OpenAI Model Configurator
# =============================================================================

class OpenAIModelConfigurator:
    """Setup API key and select an OpenAI model."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "default": "",
                    "placeholder": "Enter your OpenAI API key",
                }),
                "model_name": (OPENAI_MODELS, {
                    "default": "gpt-5.4-mini",
                }),
                "generate_audio": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Yes (Use TTS)",
                    "label_off": "No Voice",
                }),
                "voice_name": (OPENAI_VOICES, {
                    "default": "alloy",
                }),
                "reasoning_effort": (["default", "low", "medium", "high"], {
                    "default": "default"
                }),
            },
        }

    RETURN_TYPES = ("OPENAI_MODEL",)
    RETURN_NAMES = ("openai_model",)
    FUNCTION = "configure"
    CATEGORY = CATEGORY
    DESCRIPTION = "Configure the OpenAI API key, select a model, and set thinking/reasoning effort."

    def configure(self, api_key: str, model_name: str, generate_audio: bool, voice_name: str, reasoning_effort: str = "default"):
        if not api_key or not api_key.strip():
            raise ValueError("❌ API key must not be empty.")

        openai = _get_openai()
        client = openai.OpenAI(api_key=api_key.strip())

        payload = {
            "client": client,
            "model_name": model_name,
            "api_key": api_key.strip(),
            "generate_audio": generate_audio,
            "voice_name": voice_name,
            "reasoning_effort": reasoning_effort,
        }
        print(f"✅ [Universal LLM Suite] Configured OpenAI model: {model_name} (Voice: {generate_audio}, Reasoning: {reasoning_effort})")
        return (payload,)


# =============================================================================
# Node: OpenAI API Runner
# =============================================================================

class OpenAIAPIRunner:
    """Core engine – sends text (and optional vision) to OpenAI and returns
    text response (and optional audio via TTS)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "openai_model": ("OPENAI_MODEL",),
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
            },
        }

    RETURN_TYPES = ("STRING", "AUDIO",)
    RETURN_NAMES = ("response_text", "response_audio",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = "Send prompts to OpenAI and receive text (and optional audio)."

    def run(self, openai_model: dict, system_prompt: str, user_prompt: str, image_input=None):

        client = openai_model["client"]
        model_name = openai_model["model_name"]
        generate_audio = openai_model.get("generate_audio", False)
        voice_name = openai_model.get("voice_name", "alloy")

        print(f"🚀 [Universal LLM Suite] Running OpenAI model={model_name}")

        try:
            messages = []
            
            # Add system prompt (o1 models handle this differently sometimes, but standard api accepts it)
            if system_prompt.strip() and not model_name.startswith("o1-"):
                messages.append({"role": "system", "content": system_prompt})
            
            # Content definition
            content = []
            if user_prompt.strip() or model_name.startswith("o1-"): 
                # For o1, we combine system prompt if present
                if model_name.startswith("o1-") and system_prompt.strip():
                    combined_prompt = f"[System Instruction]\n{system_prompt.strip()}\n\n[User]\n{user_prompt}"
                    content.append({"type": "text", "text": combined_prompt})
                elif user_prompt.strip():
                    content.append({"type": "text", "text": user_prompt})

            if image_input is not None:
                if model_name.startswith("o1-"):
                    raise ValueError(f"❌ Model '{model_name}' does not currently support image inputs.")
                base64_image = image_tensor_to_base64_png(image_input)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })

            messages.append({"role": "user", "content": content})

            # Call OpenAI Chat Completions API
            kwargs = {
                "model": model_name,
                "messages": messages
            }
            reasoning = openai_model.get("reasoning_effort", "default")
            if reasoning != "default":
                kwargs["reasoning_effort"] = reasoning

            response = client.chat.completions.create(**kwargs)
            
            response_text = response.choices[0].message.content or ""

            # Check if we should generate TTS
            audio_dict = empty_audio()
            if generate_audio and response_text.strip():
                # Extract text without markdown code blocks etc. maybe optional but usually TTS handles it mostly ok or we just pass it
                print(f"🎙️ [Universal LLM Suite] Generating TTS Audio ({voice_name})...")
                tts_response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice_name,
                    input=response_text[:4000],  # TTS API limit is 4096 chars usually
                    response_format="pcm"  # we can request 24kHz raw PCM directly usually
                )
                
                # OpenAI raw PCM is 24kHz int16 by default
                audio_bytes = b""
                for chunk in tts_response.iter_bytes():
                    audio_bytes += chunk
                
                if audio_bytes:
                    audio_dict = pcm_bytes_to_audio_dict(audio_bytes, sample_rate=24000)

        except Exception as e:
            traceback.print_exc()
            response_text = f"❌ OpenAI API Error: {e}"
            audio_dict = empty_audio()

        return (response_text, audio_dict,)
