# =============================================================================
# Universal LLM Suite
# ComfyUI Custom Node Package
# =============================================================================

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
