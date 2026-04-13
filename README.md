# ComfyUI Universal LLM Suite

A comprehensive, all-in-one suite for seamlessly integrating Large Language Models (LLMs) like Google Gemini and OpenAI (ChatGPT) directly into your ComfyUI workflows. 

Designed for both Free and Paid API tiers, this suite provides robust tools for text generation, prompt engineering, image vision analysis, and fully-featured text-to-speech (TTS) voice capabilities.

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)

## ✨ Key Features

* **Multi-Provider Support:** Run Google Gemini and OpenAI models side-by-side in your workflow.
* **Cost-Effective Presets:** Defaults configured to prioritize highly capable but cost-effective models like `gpt-5.4-mini` and `gemini-2.5-flash-lite`.
* **Multimodal Vision:** Pass images from your ComfyUI workflow directly into the LLM API runners.
* **Native Voice (TTS):** 
  * Play, save, and manage expressive, character-driven audio generated natively by Gemini 2.5/3.0.
  * Generate high-quality voice audio from OpenAI's TTS service natively.
* **Smart UI Elements:**
  * Password-masked API key fields for safety during screen recording.
  * Resizable, copy/paste-friendly Text Display node.
  * In-browser audio playback widget.

## 📦 Nodes Included

| Category | Node Name | Description |
| :--- | :--- | :--- |
| **Config** | ✨ Gemini Configurator | Masked API key input, model selection, and Gemini voice choice (Puck, Aoede, etc.) |
| **Config** | ✨ OpenAI Configurator | Masked API key input, model selection (gpt-5.4-mini, o1-mini, etc.), and TTS voice choice. |
| **Runner** | 🚀 Gemini API Runner | Executes the prompt and optional image, returning text and audio dict (if applicable). |
| **Runner** | 🚀 OpenAI API Runner | Executes the prompt against OpenAI, returning text and audio dict (if TTS enabled). |
| **Utility** | 📝 LLM Dual Prompt | Convenient UI to structure your System Instruction and User Prompt. |
| **Output** | 📄 LLM Text Display | A resizable, auto-scrolling textarea perfectly suited for reading long LLM outputs. |
| **Output** | 🔊 LLM Audio Save & Play | Saves the generated audio tensor to your output folder and provides an in-browser "Play" button. |

## 🛠️ Installation

### Method 1: ComfyUI Manager (Recommended)
1. Open ComfyUI Manager.
2. Search for "Universal LLM Suite".
3. Click Install and restart ComfyUI.

### Method 2: Manual Install
1. Open a terminal and navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   ```
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ComfyUI-Universal-LLM-Suite.git
   ```
3. The suite will auto-install its python dependencies (`google-genai` and `openai`) upon booting ComfyUI. Restart the server once cloned.

## 📝 Usage Guide

1. **Add a Configurator:** Drop in a Configurator (Gemini or OpenAI) and paste your API Key.
2. **Setup Prompts:** Use the `LLM Dual Prompt` node to write your context.
3. **Connect to Runner:** Link the Configurator and Prompt fields to the `API Runner`.
4. **View Outputs:** Connect the `response_text` to the `LLM Text Display`, and the `response_audio` to the `LLM Audio Save & Play`.

*(Tip: Both the Gemini and OpenAI configurators have a "Reload Model" button to quickly apply API Key changes without restarting ComfyUI).*

## ⚠️ Notes on Gemini Voice Capabilities

Currently, the Google explicitly restricts its highly expressive *Gen-Audio* voices to a set of specific mythological personas (e.g., Puck, Charon, Kore, Fenrir, Aoede) when using native bidirectional/multimodal APIs. These are specifically tuned for dramatic reading and virtual personalities, unlike the robotic voices from typical TTS systems.

## 📄 License
MIT License
