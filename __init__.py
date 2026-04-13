# =============================================================================
# Universal LLM Suite
# ComfyUI Custom Node Package
# =============================================================================

import sys
import subprocess

def ensure_dependencies():
    """Auto-install missing dependencies on first load."""
    packages = ["google-genai", "openai"]
    for pkg in packages:
        try:
            if pkg == "google-genai":
                import google.genai
            elif pkg == "openai":
                import openai
        except ImportError:
            print(f"📦 [Universal LLM Suite] Installing missing package: {pkg}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.DEVNULL,
                )
                print(f"✅ [Universal LLM Suite] Successfully installed {pkg}")
            except Exception as e:
                print(f"❌ [Universal LLM Suite] Failed to install {pkg}: {e}")

# Run dependency check immediately before loading nodes
ensure_dependencies()

from .nodes_base import (
    LLMDualPrompt,
    LLMTextDisplay,
    LLMAudioSavePlay,
)
from .gemini_nodes import (
    GeminiModelConfigurator,
    GeminiAPIRunner,
)
from .openai_nodes import (
    OpenAIModelConfigurator,
    OpenAIAPIRunner,
)

NODE_CLASS_MAPPINGS = {
    "LLMDualPrompt": LLMDualPrompt,
    "LLMTextDisplay": LLMTextDisplay,
    "LLMAudioSavePlay": LLMAudioSavePlay,
    "GeminiModelConfigurator": GeminiModelConfigurator,
    "GeminiAPIRunner": GeminiAPIRunner,
    "OpenAIModelConfigurator": OpenAIModelConfigurator,
    "OpenAIAPIRunner": OpenAIAPIRunner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LLMDualPrompt": "📝 LLM Dual Prompt",
    "LLMTextDisplay": "📄 LLM Text Display",
    "LLMAudioSavePlay": "🔊 LLM Audio Save & Play",
    "GeminiModelConfigurator": "✨ Gemini Configurator",
    "GeminiAPIRunner": "🚀 Gemini API Runner",
    "OpenAIModelConfigurator": "✨ OpenAI Configurator",
    "OpenAIAPIRunner": "🚀 OpenAI API Runner",
}

WEB_DIRECTORY = "./web/js"

__version__ = "1.1.0"

print(f"✅ Universal LLM Suite v{__version__} loaded")
