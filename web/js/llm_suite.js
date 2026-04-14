import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// =============================================================================
// Universal LLM Suite – Frontend JS
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// 1. Model Configurators
//    - API Key: masked with ● dots (password-style)
//    - Removed unnecessary separator widget
//    - Reload button
// ─────────────────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "UniversalLLMSuite.ModelConfigurator",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "GeminiModelConfigurator" && nodeData.name !== "OpenAIModelConfigurator") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            if (this._llmConfigured) return r;
            this._llmConfigured = true;

            // ── Mask the api_key widget with custom draw (Legacy Canvas UI) ──
            const apiWidget = this.widgets?.find(w => w.name === "api_key");
            if (apiWidget) {
                apiWidget.draw = function (ctx, node, widget_width, y, H) {
                    const margin = 15;
                    const drawW = widget_width - margin * 2;

                    // Clip everything to the widget area
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) {
                        ctx.roundRect(margin, y, drawW, H, [4]);
                    } else {
                        ctx.rect(margin, y, drawW, H);
                    }
                    ctx.clip();

                    // Background
                    ctx.fillStyle = "#1e1e2e";
                    ctx.fillRect(margin, y, drawW, H);

                    // Border (draw after fill, inside clip)
                    ctx.strokeStyle = "rgba(255,255,255,0.12)";
                    ctx.lineWidth = 1;
                    ctx.strokeRect(margin, y, drawW, H);

                    // Label
                    ctx.fillStyle = "#8888aa";
                    ctx.font = "11px sans-serif";
                    ctx.textAlign = "left";
                    ctx.fillText("🔑 API Key", margin + 10, y + H * 0.65);

                    // Value: show ● dots or placeholder (clipped to widget)
                    if (this.value && this.value.length > 0) {
                        ctx.fillStyle = "#aaaacc";
                        ctx.font = "14px sans-serif";
                        // Calculate how many dots fit in the available space
                        const labelWidth = 80; // approx width of "🔑 API Key"
                        const availableW = drawW - labelWidth - 20;
                        const singleDot = ctx.measureText("●").width;
                        const maxDots = Math.max(1, Math.floor(availableW / singleDot));
                        const dotCount = Math.min(this.value.length, maxDots);
                        const dots = "●".repeat(dotCount);
                        ctx.textAlign = "right";
                        ctx.fillText(dots, margin + drawW - 10, y + H * 0.68);
                    } else {
                        ctx.fillStyle = "#555";
                        ctx.font = "11px sans-serif";
                        ctx.textAlign = "right";
                        ctx.fillText("Click to enter key…", margin + drawW - 10, y + H * 0.65);
                    }

                    ctx.restore(); // Remove clip
                };

                // ── Mask for Nodes 2.0 / DOM-based UI ──
                // Convert any <input> element for api_key to password type
                const maskDomInputs = () => {
                    if (apiWidget.element) {
                        const inputs = apiWidget.element.querySelectorAll
                            ? apiWidget.element.querySelectorAll("input[type='text']")
                            : [];
                        inputs.forEach(inp => { inp.type = "password"; });
                        // If the widget element itself is an input
                        if (apiWidget.element.tagName === "INPUT" && apiWidget.element.type === "text") {
                            apiWidget.element.type = "password";
                        }
                    }
                    // Also check the node's DOM element for any input with matching data attributes
                    const nodeEl = this.domElement || this.element;
                    if (nodeEl) {
                        nodeEl.querySelectorAll("input").forEach(inp => {
                            if (inp.dataset?.widgetName === "api_key" ||
                                inp.name === "api_key" ||
                                inp.placeholder?.toLowerCase().includes("api key")) {
                                inp.type = "password";
                            }
                        });
                    }
                };
                // Run immediately and also observe for late DOM creation
                setTimeout(maskDomInputs, 100);
                setTimeout(maskDomInputs, 500);
                setTimeout(maskDomInputs, 1500);
            }

            // ── Reload Button (no separator) ──
            if (!this.widgets?.some(w => w.name === "🔄 Reload Model")) {
                this.addWidget("button", "🔄 Reload Model", "reload", () => {
                    this.setDirtyCanvas(true, true);
                    app.graph.setDirtyCanvas(true, true);
                    alert("✅ Model configuration reloaded.\nRun the queue again to apply.");
                });
            }

            this.setSize([340, this.computeSize()[1]]);
            return r;
        };
    },
});


// ─────────────────────────────────────────────────────────────────────────────
// 2. LLM Text Display
//    - DOM-based scrollable textarea (full text visible, scroll for long text)
//    - Copy / Select All buttons for easy clipboard use
// ─────────────────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "UniversalLLMSuite.TextDisplay",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "LLMTextDisplay") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            if (this._llmTextConfigured) return r;
            this._llmTextConfigured = true;

            // ── Container ──
            const container = document.createElement("div");
            container.style.cssText = `
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                gap: 5px;
                box-sizing: border-box;
            `;

            // ── Textarea ──
            const textarea = document.createElement("textarea");
            textarea.readOnly = true;
            textarea.value = "Waiting for response…";
            textarea.style.cssText = `
                width: 100%;
                flex-grow: 1;
                box-sizing: border-box;
                padding: 12px 14px;
                font-family: 'Meiryo', 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.7;
                color: #e2e8f0;
                background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid rgba(100,149,237,0.2);
                border-radius: 8px;
                resize: none;
                outline: none;
                overflow-y: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            `;
            textarea.addEventListener("focus", () => {
                textarea.style.borderColor = "rgba(100,149,237,0.5)";
            });
            textarea.addEventListener("blur", () => {
                textarea.style.borderColor = "rgba(100,149,237,0.2)";
            });

            // ── Button row ──
            const btnRow = document.createElement("div");
            btnRow.style.cssText = `
                display: flex;
                gap: 6px;
                justify-content: flex-end;
                flex-shrink: 0;
            `;

            const makeBtnStyle = () => `
                padding: 5px 12px;
                font-size: 11px;
                color: #cbd5e0;
                background: #2d3748;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.15s;
            `;

            // Select All
            const selectBtn = document.createElement("button");
            selectBtn.textContent = "🔍 Select All";
            selectBtn.style.cssText = makeBtnStyle();
            selectBtn.addEventListener("click", () => {
                textarea.select();
                textarea.focus();
            });
            selectBtn.addEventListener("mouseover", () => { selectBtn.style.background = "#4a5568"; });
            selectBtn.addEventListener("mouseout",  () => { selectBtn.style.background = "#2d3748"; });

            // Copy
            const copyBtn = document.createElement("button");
            copyBtn.textContent = "📋 Copy";
            copyBtn.style.cssText = makeBtnStyle();
            copyBtn.addEventListener("click", () => {
                navigator.clipboard.writeText(textarea.value).then(() => {
                    copyBtn.textContent = "✅ Copied!";
                    copyBtn.style.background = "#2f855a";
                    setTimeout(() => {
                        copyBtn.textContent = "📋 Copy";
                        copyBtn.style.background = "#2d3748";
                    }, 1500);
                }).catch(() => {
                    // Fallback: select all so user can Ctrl+C
                    textarea.select();
                    textarea.focus();
                });
            });
            copyBtn.addEventListener("mouseover", () => { copyBtn.style.background = "#4a5568"; });
            copyBtn.addEventListener("mouseout",  () => { copyBtn.style.background = "#2d3748"; });

            btnRow.appendChild(selectBtn);
            btnRow.appendChild(copyBtn);
            container.appendChild(textarea);
            container.appendChild(btnRow);

            this._geminiTextArea = textarea;

            // ── Add as DOM widget ──
            // Height is relative to the node size so resizing the node
            // automatically grows / shrinks the text area.
            const self = this;
            this.addDOMWidget("display_text", "custom", container, {
                getValue: () => textarea.value,
                setValue: (v) => { textarea.value = v || ""; },
                getMinHeight: () => {
                    // Reserve space for title bar (~40px) and button row (~36px)
                    const overhead = 76;
                    const nodeH = self.size?.[1] ?? 340;
                    return Math.max(60, nodeH - overhead);
                },
            });

            this.setSize([440, 340]);
            return r;
        };

        // ── Update text on execution ──
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            if (message?.text && message.text.length > 0) {
                const responseText = message.text[0];
                if (this._llmTextArea) {
                    this._llmTextArea.value = responseText;
                    // Scroll to top so user sees the beginning
                    this._llmTextArea.scrollTop = 0;
                }
                const w = this.widgets?.find(w => w.name === "display_text");
                if (w && w.value !== undefined) {
                    w.value = responseText;
                }
                this.setDirtyCanvas(true, true);
            }
        };

        // ── Cleanup ──
        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            onRemoved?.apply(this, arguments);
            // Remove legacy overlay if present
            if (this._geminiTextContainer) {
                this._geminiTextContainer.remove();
                this._geminiTextContainer = null;
            }
        };
    },
});


// ─────────────────────────────────────────────────────────────────────────────
// 3. Universal Audio Save & Play
//    - Play / Stop buttons
//    - Status and saved filename display
// ─────────────────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "UniversalLLMSuite.AudioSavePlay",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "LLMAudioSavePlay") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            if (this.widgets?.some(w => w.name === "▶ Play Audio")) return r;

            // Status label
            this._audioStatusWidget = this.addWidget("text", "status", "⏳ No audio yet", () => {}, {
                serialize: false,
            });

            // Saved filename label
            this._savedFileWidget = this.addWidget("text", "saved_file", "", () => {}, {
                serialize: false,
            });

            this._audioElement = null;
            this._audioUrl = null;

            // Play button
            this.addWidget("button", "▶ Play Audio", "play", () => {
                if (!this._audioUrl) {
                    alert("⚠️ No audio available. Run the workflow first.");
                    return;
                }
                if (this._audioElement) {
                    this._audioElement.pause();
                    this._audioElement.currentTime = 0;
                }
                this._audioElement = new Audio(this._audioUrl);
                this._audioElement.play().catch(err => {
                    console.error("[Universal LLM Suite] Audio play error:", err);
                    alert("❌ Could not play audio.\n" + err);
                });

                if (this._audioStatusWidget) {
                    this._audioStatusWidget.value = "🔊 Playing...";
                    this.setDirtyCanvas(true, true);
                }

                this._audioElement.onended = () => {
                    if (this._audioStatusWidget) {
                        this._audioStatusWidget.value = "✅ Playback finished";
                        this.setDirtyCanvas(true, true);
                    }
                };
            });

            // Stop button
            this.addWidget("button", "⏹ Stop", "stop", () => {
                if (this._audioElement) {
                    this._audioElement.pause();
                    this._audioElement.currentTime = 0;
                    if (this._audioStatusWidget) {
                        this._audioStatusWidget.value = "⏹ Stopped";
                        this.setDirtyCanvas(true, true);
                    }
                }
            });

            this.setSize([320, 200]);
            return r;
        };

        // ── Update on execution ──
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            if (message?.audio_path && message.audio_path.length > 0) {
                const path = message.audio_path[0];
                if (path) {
                    this._audioUrl = `${window.location.origin}${path}`;
                    if (this._audioStatusWidget) {
                        this._audioStatusWidget.value = "✅ Audio ready – press Play";
                    }
                } else {
                    this._audioUrl = null;
                    if (this._audioStatusWidget) {
                        this._audioStatusWidget.value = "⚠️ No audio data received";
                    }
                }
            }
            if (message?.audio_filename && message.audio_filename.length > 0) {
                const fn = message.audio_filename[0];
                if (fn && this._savedFileWidget) {
                    this._savedFileWidget.value = "💾 " + fn;
                }
            }

            this.setDirtyCanvas(true, true);
        };
    },
});
