/**
 * UNACH AI - Client Application Logic
 * Interactive Chat, Voice Recognition, Speech Synthesis, Settings & Modal Management
 */

// Application State
const AppState = {
    selectedCategory: "all",
    activeMode: "gemini",
    hasGeminiKey: false,
    isProcessing: false,
    isListening: false,
    documentsData: null
};

// DOM Elements
const Elements = {
    chatHistory: document.getElementById("chatHistory"),
    welcomeHero: document.getElementById("welcomeHero"),
    chatInput: document.getElementById("chatInput"),
    btnSend: document.getElementById("btnSend"),
    btnMic: document.getElementById("btnMic"),
    categoryBtns: document.querySelectorAll(".category-btn"),
    quickQItems: document.querySelectorAll(".quick-q-item"),
    quickQList: document.querySelector(".quick-questions-list"),
    activeCategoryPill: document.getElementById("activeCategoryPill"),
    activeCategoryText: document.getElementById("activeCategoryText"),
    btnClearCategory: document.getElementById("btnClearCategory"),
    modeChip: document.getElementById("modeChip"),
    modeLabel: document.getElementById("modeLabel"),
    docCountPill: document.getElementById("docCountPill"),
    // Modals
    settingsModal: document.getElementById("settingsModal"),
    btnOpenSettings: document.getElementById("btnOpenSettings"),
    btnCloseSettings: document.getElementById("btnCloseSettings"),
    docsModal: document.getElementById("docsModal"),
    btnOpenDocs: document.getElementById("btnOpenDocs"),
    btnCloseDocs: document.getElementById("btnCloseDocs"),
    docSearchInput: document.getElementById("docSearchInput"),
    docListContainer: document.getElementById("docListContainer"),
    // Settings Form
    geminiKeyInput: document.getElementById("geminiKeyInput"),
    btnTestKey: document.getElementById("btnTestKey"),
    testKeyResult: document.getElementById("testKeyResult"),
    btnSaveSettings: document.getElementById("btnSaveSettings"),
    modeCards: document.querySelectorAll(".mode-option-card"),
    btnReindex: document.getElementById("btnReindex"),
    reindexStatus: document.getElementById("reindexStatus")
};

// Category Specific Quick Questions
const CategoryQuestions = {
    all: [
        { label: "🤝 Requisitos para Servicio Social y créditos necesarios", q: "¿Cuáles son los requisitos y porcentaje de créditos para iniciar el Servicio Social en la UNACH?" },
        { label: "⚖️ Derechos y obligaciones como estudiante", q: "¿Cuáles son los derechos y deberes fundamentales de los alumnos según el Estatuto Integral de la UNACH?" },
        { label: "🤖 Reglas sobre el uso de Inteligencia Artificial (IA)", q: "¿Cuáles son los lineamientos éticos para el uso responsable de la Inteligencia Artificial en tareas y proyectos?" },
        { label: "⚠️ Faltas disciplinarias y sanciones", q: "¿Qué causas ameritan una sanción o baja temporal según el Estatuto?" },
        { label: "🏛️ Procedimiento ante el Tribunal Universitario", q: "¿Cómo funciona el Tribunal Universitario y cómo puedo presentar una queja o inconformidad?" },
        { label: "🛡️ Protocolo contra acoso y violencia de género", q: "¿Cuál es el protocolo de actuación ante situaciones de acoso o violencia de género en la UNACH?" }
    ],
    servicio_social: [
        { label: "📋 Porcentaje de créditos necesarios", q: "¿Cuántos créditos o qué porcentaje necesito para iniciar mi servicio social en la UNACH?" },
        { label: "⏱️ Horas obligatorias y plazos", q: "¿Cuántas horas de servicio social debo cumplir y en qué tiempo como mínimo según el reglamento?" },
        { label: "🚫 Causas de cancelación o sanción", q: "¿Cuáles son los motivos de cancelación, suspensión o sanción en el servicio social?" },
        { label: "📜 Requisitos de carta de liberación", q: "¿Cuáles son los requisitos y pasos para tramitar la carta de liberación de servicio social?" }
    ],
    alumnos_derechos: [
        { label: "⚖️ Derechos fundamentales del alumno", q: "¿Cuáles son mis derechos fundamentales según el Estatuto Integral de la UNACH?" },
        { label: "⏳ Plazos para solicitar baja temporal", q: "¿Cuáles son los requisitos y plazos para solicitar una baja temporal según el Estatuto?" },
        { label: "🚫 Causas de baja definitiva", q: "¿Por qué causas un estudiante puede causar baja definitiva de la UNACH según el Estatuto?" },
        { label: "🤖 Reglas para el uso de IA en tareas", q: "¿Qué lineamientos existen en la UNACH para el uso ético y responsable de la Inteligencia Artificial?" }
    ],
    academico_facultades: [
        { label: "🏥 Reglamento de Medicina Humana", q: "¿Qué faltas disciplinarias y sanciones contempla el reglamento de la Facultad de Medicina Humana?" },
        { label: "🩺 Internado y asignaturas clínicas", q: "¿Cuáles son los requisitos de acreditación de asignaturas clínicas e internado médico?" },
        { label: "📚 Planeación académica docente", q: "¿Cómo se organiza la planeación académica docente y las academias en la UNACH?" }
    ],
    normatividad_tribunal: [
        { label: "🏛️ Quejas ante el Tribunal Universitario", q: "¿Cómo funciona el Tribunal Universitario de la UNACH y cómo puedo presentar una queja?" },
        { label: "🚨 Medidas de seguridad en campus", q: "¿Cuáles son los lineamientos de seguridad vigentes en los campus de la UNACH?" },
        { label: "⚖️ Comisión Mixta Permanente", q: "¿Qué funciones tiene la Comisión Mixta Permanente según la normatividad?" }
    ],
    formatos_administrativos: [
        { label: "📑 Lineamientos de Entrega Recepción", q: "¿Cuáles son los lineamientos y anexos para el proceso de entrega recepción en la UNACH?" },
        { label: "📝 Instructivos de llenado", q: "¿Qué formatos e instructivos de llenado existen para actas administrativas de personal?" }
    ]
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {
    initEventListeners();
    await loadSettings();
    await loadDocumentsCatalog();
});

function initEventListeners() {
    // Chat Send
    Elements.btnSend.addEventListener("click", () => handleSendMessage());
    Elements.chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-expand textarea
    Elements.chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = Math.min(this.scrollHeight, 120) + "px";
    });

    // Microphone (Voice Recognition)
    if (Elements.btnMic) {
        Elements.btnMic.addEventListener("click", toggleSpeechRecognition);
    }

    // Category Filter Selection
    Elements.categoryBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const catId = btn.getAttribute("data-category") || "all";
            const catName = btn.querySelector("span:last-child")?.textContent.trim() || catId;
            selectCategory(catId, catName);
        });
    });

    // Clear Category Filter Button
    if (Elements.btnClearCategory) {
        Elements.btnClearCategory.addEventListener("click", () => {
            selectCategory("all", "Todos los Reglamentos");
        });
    }

    // Setup initial Quick Questions clicks
    setupQuickQuestionListeners();

    // Hero Topic Cards
    document.querySelectorAll(".hero-card").forEach(card => {
        card.addEventListener("click", () => {
            const prompt = card.getAttribute("data-prompt");
            if (prompt) {
                Elements.chatInput.value = prompt;
                handleSendMessage();
            }
        });
    });

    // Modals Open/Close
    if (Elements.btnOpenSettings) Elements.btnOpenSettings.addEventListener("click", () => openModal(Elements.settingsModal));
    Elements.btnCloseSettings.addEventListener("click", () => closeModal(Elements.settingsModal));
    Elements.modeChip.addEventListener("click", () => openModal(Elements.settingsModal));

    Elements.btnOpenDocs.addEventListener("click", () => openModal(Elements.docsModal));
    Elements.btnCloseDocs.addEventListener("click", () => closeModal(Elements.docsModal));

    // Settings Mode Options
    if (Elements.modeCards) {
        Elements.modeCards.forEach(card => {
            card.addEventListener("click", () => {
                Elements.modeCards.forEach(c => c.classList.remove("selected"));
                card.classList.add("selected");
            });
        });
    }

    // Test Gemini Key
    if (Elements.btnTestKey) Elements.btnTestKey.addEventListener("click", handleTestGeminiKey);

    // Save Settings
    if (Elements.btnSaveSettings) Elements.btnSaveSettings.addEventListener("click", handleSaveSettings);

    // Reindex Button
    if (Elements.btnReindex) Elements.btnReindex.addEventListener("click", handleReindex);

    // Document Search Filter
    if (Elements.docSearchInput) {
        Elements.docSearchInput.addEventListener("input", (e) => {
            filterDocumentsList(e.target.value);
        });
    }

    // Close modal on background click
    [Elements.settingsModal, Elements.docsModal].forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeModal(modal);
        });
    });

    // New Chat / Clear consultation button
    const btnNewChat = document.getElementById("btnNewChat");
    if (btnNewChat) {
        btnNewChat.addEventListener("click", () => {
            const rows = Elements.chatHistory.querySelectorAll(".message-row");
            rows.forEach(r => r.remove());
            if (Elements.welcomeHero) {
                Elements.welcomeHero.style.display = "block";
            }
            Elements.chatInput.value = "";
            Elements.chatInput.focus();
            showToast("Nueva consulta iniciada");
        });
    }
}

function selectCategory(catId, catName) {
    AppState.selectedCategory = catId;

    // Update active button styles
    Elements.categoryBtns.forEach(b => {
        if (b.getAttribute("data-category") === catId) {
            b.classList.add("active");
        } else {
            b.classList.remove("active");
        }
    });

    // Update active category pill above input
    if (Elements.activeCategoryPill) {
        if (catId === "all") {
            Elements.activeCategoryPill.style.display = "none";
        } else {
            Elements.activeCategoryPill.style.display = "inline-flex";
            Elements.activeCategoryText.textContent = `🏷️ Área activa: ${catName}`;
        }
    }

    // Update quick questions dynamically
    const questions = CategoryQuestions[catId] || CategoryQuestions.all;
    if (Elements.quickQList) {
        Elements.quickQList.innerHTML = questions.map(item => `
            <div class="quick-q-item" data-question="${escapeHtml(item.q)}">
                ${escapeHtml(item.label)}
            </div>
        `).join("");
        setupQuickQuestionListeners();
    }

    if (catId !== "all") {
        showToast(`Filtro activado: ${catName}`);
    }
}

function setupQuickQuestionListeners() {
    document.querySelectorAll(".quick-q-item").forEach(item => {
        item.addEventListener("click", () => {
            const question = item.getAttribute("data-question") || item.textContent.trim();
            Elements.chatInput.value = question;
            handleSendMessage();
            if (window.innerWidth <= 900) {
                closeSidebar();
            }
        });
    });
}

// ==========================================================================
// Settings Management
// ==========================================================================
async function loadSettings() {
    try {
        const settings = await API.getSettings();
        AppState.activeMode = settings.mode;
        AppState.hasGeminiKey = settings.has_gemini_key;

        updateModeUI(settings.mode, settings.has_gemini_key);

        // Pre-fill modal if element exists
        if (Elements.geminiKeyInput && settings.masked_key) {
            Elements.geminiKeyInput.placeholder = `Actual: ${settings.masked_key} (deja vacío para no cambiar)`;
        }

        if (Elements.modeCards) {
            Elements.modeCards.forEach(card => {
                if (card.getAttribute("data-mode") === settings.mode) {
                    card.classList.add("selected");
                } else {
                    card.classList.remove("selected");
                }
            });
        }
    } catch (err) {
        console.error("Error loading settings:", err);
    }
}

function updateModeUI(mode, hasKey) {
    if (!Elements.modeLabel) return;
    if (mode === "gemini" && hasKey) {
        Elements.modeLabel.textContent = "🟢 Asistente UNACH Activo";
        if (Elements.modeChip) Elements.modeChip.style.borderColor = "var(--unach-gold-400)";
    } else {
        Elements.modeLabel.textContent = "🟢 Asistente UNACH (Offline)";
        if (Elements.modeChip) Elements.modeChip.style.borderColor = "var(--border-glass)";
    }
}

async function handleSaveSettings() {
    const selectedModeCard = document.querySelector(".mode-option-card.selected");
    const mode = selectedModeCard ? selectedModeCard.getAttribute("data-mode") : "gemini";
    const key = Elements.geminiKeyInput.value.trim();

    try {
        Elements.btnSaveSettings.disabled = true;
        Elements.btnSaveSettings.textContent = "Guardando...";

        const payload = { mode };
        if (key) {
            payload.gemini_api_key = key;
        }

        const res = await API.updateSettings(payload);
        AppState.activeMode = res.mode;
        AppState.hasGeminiKey = res.has_gemini_key;
        updateModeUI(res.mode, res.has_gemini_key);

        showToast("Configuración guardada exitosamente");
        closeModal(Elements.settingsModal);
    } catch (err) {
        alert("Error al guardar: " + err.message);
    } finally {
        Elements.btnSaveSettings.disabled = false;
        Elements.btnSaveSettings.textContent = "Guardar Cambios";
    }
}

async function handleTestGeminiKey() {
    const key = Elements.geminiKeyInput.value.trim();
    Elements.testKeyResult.style.display = "block";
    Elements.testKeyResult.textContent = "Probando conexión con Google AI Studio...";
    Elements.testKeyResult.style.color = "var(--text-muted)";

    try {
        const res = await API.testConnection(key);
        if (res.success) {
            Elements.testKeyResult.textContent = "✅ " + res.message;
            Elements.testKeyResult.style.color = "var(--accent-emerald)";
        } else {
            Elements.testKeyResult.textContent = "❌ " + res.error;
            Elements.testKeyResult.style.color = "var(--accent-rose)";
        }
    } catch (err) {
        Elements.testKeyResult.textContent = "❌ Error: " + err.message;
        Elements.testKeyResult.style.color = "var(--accent-rose)";
    }
}

// ==========================================================================
// Document Catalog & Reindexing
// ==========================================================================
async function loadDocumentsCatalog() {
    try {
        const data = await API.getDocuments();
        AppState.documentsData = data;

        if (Elements.docCountPill) {
            Elements.docCountPill.textContent = `📚 ${data.total_documents} Documentos • ${data.total_chunks} Artículos`;
        }

        const heroDocCountBadge = document.getElementById("heroDocCountBadge");
        if (heroDocCountBadge) {
            heroDocCountBadge.textContent = `✓ ${data.total_documents} Documentos Oficiales`;
        }

        renderDocumentsList(data.documents);
    } catch (err) {
        console.error("Error loading documents:", err);
    }
}

function renderDocumentsList(documents) {
    if (!Elements.docListContainer) return;

    if (!documents || documents.length === 0) {
        Elements.docListContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No se encontraron documentos indexados.</div>`;
        return;
    }

    Elements.docListContainer.innerHTML = documents.map(doc => `
        <div class="doc-item-row">
            <div class="doc-meta">
                <span class="doc-name">${escapeHtml(doc.title)}</span>
                <span class="doc-sub">${doc.total_pages} páginas • ${doc.total_chunks} fragmentos • Categoría: <b>${doc.category}</b></span>
            </div>
            <span class="doc-format-pill">${doc.format}</span>
        </div>
    `).join("");
}

function filterDocumentsList(searchTerm) {
    if (!AppState.documentsData || !AppState.documentsData.documents) return;
    const term = searchTerm.toLowerCase().trim();
    const filtered = AppState.documentsData.documents.filter(d => 
        d.title.toLowerCase().includes(term) || 
        d.filename.toLowerCase().includes(term) ||
        d.category.toLowerCase().includes(term)
    );
    renderDocumentsList(filtered);
}

async function handleReindex() {
    if (!confirm("¿Deseas volver a indexar todos los documentos de la carpeta? Esto puede tomar unos momentos.")) return;

    try {
        Elements.btnReindex.disabled = true;
        Elements.reindexStatus.style.display = "block";
        Elements.reindexStatus.textContent = "Indexando documentos oficiales de la UNACH...";

        const res = await API.reindex();
        Elements.reindexStatus.textContent = `✅ Listo: ${res.total_documents} documentos y ${res.total_chunks} artículos indexados.`;
        Elements.reindexStatus.style.color = "var(--accent-emerald)";

        await loadDocumentsCatalog();
    } catch (err) {
        Elements.reindexStatus.textContent = "❌ Error: " + err.message;
        Elements.reindexStatus.style.color = "var(--accent-rose)";
    } finally {
        Elements.btnReindex.disabled = false;
    }
}

// ==========================================================================
// Chat Flow & Message Rendering
// ==========================================================================
let loadingInterval = null;

async function handleSendMessage() {
    if (AppState.isProcessing) return;

    const query = Elements.chatInput.value.trim();
    if (!query) return;

    // Clear input
    Elements.chatInput.value = "";
    Elements.chatInput.style.height = "auto";

    // Hide welcome hero if first message
    if (Elements.welcomeHero) {
        Elements.welcomeHero.style.display = "none";
    }

    // Append User Message
    appendUserMessage(query);

    // Append Assistant Loading Bubble
    const loaderId = appendLoadingIndicator();

    AppState.isProcessing = true;
    Elements.btnSend.disabled = true;

    try {
        const response = await API.askQuestion(query, AppState.selectedCategory);
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }
        removeElementById(loaderId);
        appendAssistantMessage(response);
    } catch (err) {
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }
        removeElementById(loaderId);
        appendErrorMessage(err.message);
    } finally {
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }
        AppState.isProcessing = false;
        Elements.btnSend.disabled = false;
        Elements.chatInput.focus();
    }
}

function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user";
    row.innerHTML = `
        <div class="message-bubble">
            <p>${escapeHtml(text)}</p>
        </div>
        <div class="message-avatar user">TÚ</div>
    `;
    Elements.chatHistory.appendChild(row);
    scrollToBottom();
}

function appendLoadingIndicator() {
    const id = "loader_" + Date.now();
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.id = id;
    
    // Native Animated SVG Bouncing Wave + Step Rotator + Progress Bar
    row.innerHTML = `
        <div class="message-avatar assistant">
            <img src="/static/img/unach_logo.png" alt="UNACH" class="avatar-crest-img">
        </div>
        <div class="message-bubble loader-bubble" style="min-width: 280px; padding: 0.95rem 1.25rem;">
            <div class="typing-indicator" style="display: flex; align-items: center; gap: 0.85rem;">
                <!-- Native SVG Bouncing Wave: Animates directly in the browser GPU without relying on cached CSS -->
                <svg width="44" height="24" viewBox="0 0 120 40" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0; overflow: visible;">
                    <circle cx="20" cy="20" r="10" fill="#d4a340">
                        <animate attributeName="cy" dur="0.85s" repeatCount="indefinite" values="24;8;24" keyTimes="0;0.5;1" />
                        <animate attributeName="r" dur="0.85s" repeatCount="indefinite" values="8;13;8" keyTimes="0;0.5;1" />
                        <animate attributeName="fill" dur="0.85s" repeatCount="indefinite" values="#d4a340;#fde047;#d4a340" keyTimes="0;0.5;1" />
                    </circle>
                    <circle cx="60" cy="20" r="10" fill="#e2b755">
                        <animate attributeName="cy" dur="0.85s" begin="0.2s" repeatCount="indefinite" values="24;8;24" keyTimes="0;0.5;1" />
                        <animate attributeName="r" dur="0.85s" begin="0.2s" repeatCount="indefinite" values="8;13;8" keyTimes="0;0.5;1" />
                        <animate attributeName="fill" dur="0.85s" begin="0.2s" repeatCount="indefinite" values="#d4a340;#fde047;#d4a340" keyTimes="0;0.5;1" />
                    </circle>
                    <circle cx="100" cy="20" r="10" fill="#f5cf76">
                        <animate attributeName="cy" dur="0.85s" begin="0.4s" repeatCount="indefinite" values="24;8;24" keyTimes="0;0.5;1" />
                        <animate attributeName="r" dur="0.85s" begin="0.4s" repeatCount="indefinite" values="8;13;8" keyTimes="0;0.5;1" />
                        <animate attributeName="fill" dur="0.85s" begin="0.4s" repeatCount="indefinite" values="#d4a340;#fde047;#d4a340" keyTimes="0;0.5;1" />
                    </circle>
                </svg>

                <div style="display: flex; flex-direction: column; gap: 6px; flex: 1;">
                    <span id="loadingStepText" style="font-size: 0.82rem; font-weight: 600; color: #f5cf76; transition: opacity 0.2s ease;">
                        🔍 Analizando tu consulta...
                    </span>
                    <div style="height: 3px; width: 100%; max-width: 200px; background: rgba(212, 163, 64, 0.18); border-radius: 3px; overflow: hidden; position: relative;">
                        <div class="loader-line-pulse"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    Elements.chatHistory.appendChild(row);
    scrollToBottom();

    // Rotate status messages every 1.3s so the user visually sees active progression
    const steps = [
        "🔍 Analizando tu consulta...",
        "📚 Buscando en los 35 reglamentos oficiales...",
        "⚖️ Extrayendo artículos y normativas UNACH...",
        "✍️ Redactando respuesta oficial para ti..."
    ];
    let stepIndex = 0;
    if (loadingInterval) clearInterval(loadingInterval);
    loadingInterval = setInterval(() => {
        stepIndex = (stepIndex + 1) % steps.length;
        const textEl = document.getElementById("loadingStepText");
        if (textEl) {
            textEl.style.opacity = "0.25";
            setTimeout(() => {
                if (textEl) {
                    textEl.textContent = steps[stepIndex];
                    textEl.style.opacity = "1";
                }
            }, 180);
        }
    }, 1300);

    return id;
}

function appendAssistantMessage(data) {
    const row = document.createElement("div");
    row.className = "message-row assistant";

    const formattedAnswer = parseMarkdown(data.answer);
    const modelTag = data.engine === "gemini" ? "🌟 Gemini Flash" : "⚡ Motor Local Offline";
    const latency = data.elapsed_ms ? `${(data.elapsed_ms / 1000).toFixed(2)}s` : "";

    // Sources accordion HTML
    let sourcesHtml = "";
    if (data.sources && data.sources.length > 0) {
        const sourceCards = data.sources.map((s, i) => `
            <div class="source-card">
                <div class="source-card-header">
                    <span>📄 ${escapeHtml(s.document_title || s.document)}</span>
                    <span class="source-card-badge">${escapeHtml(s.article_ref || `Pág. ${s.page}`)}</span>
                </div>
                <div class="source-card-snippet">«${escapeHtml(s.snippet)}»</div>
            </div>
        `).join("");

        sourcesHtml = `
            <div class="sources-drawer">
                <button class="sources-toggle" onclick="toggleSourcesDrawer(this)">
                    <span>📚 Ver Fuentes y Artículos UNACH (${data.sources.length})</span>
                    <span class="toggle-arrow">▼</span>
                </button>
                <div class="sources-content" style="display: none;">
                    ${sourceCards}
                </div>
            </div>
        `;
    }

    // Dynamic suggestions pills
    let suggestionsHtml = "";
    if (data.suggestions && data.suggestions.length > 0) {
        const pills = data.suggestions.map(sug => `
            <button class="suggestion-pill" onclick="askSuggestedQuestion('${escapeHtml(sug)}')">
                ${escapeHtml(sug)}
            </button>
        `).join("");

        suggestionsHtml = `
            <div class="response-suggestions">
                <div style="font-size: 0.72rem; color: var(--text-muted); width: 100%; margin-bottom: 2px;">Preguntas sugeridas:</div>
                ${pills}
            </div>
        `;
    }

    const messageId = "msg_" + Date.now();

    row.innerHTML = `
        <div class="message-avatar assistant">
            <img src="/static/img/unach_logo.png" alt="UNACH" class="avatar-crest-img">
        </div>
        <div class="message-bubble" id="${messageId}">
            <div class="message-header">
                <span class="message-model-tag">${modelTag}</span>
                <span class="message-time">${latency}</span>
            </div>
            <div class="message-content">
                ${formattedAnswer}
            </div>
            ${sourcesHtml}
            ${suggestionsHtml}
            <div class="message-actions">
                <button class="action-btn" onclick="copyMessageText('${messageId}')" title="Copiar respuesta">
                    📋 Copiar
                </button>
                <button class="action-btn" onclick="readAloudMessage('${messageId}')" title="Escuchar respuesta">
                    🔊 Escuchar
                </button>
            </div>
        </div>
    `;

    Elements.chatHistory.appendChild(row);
    scrollToBottom();
}

function appendErrorMessage(errorText) {
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.innerHTML = `
        <div class="message-avatar assistant" style="background: var(--accent-rose);">⚠️</div>
        <div class="message-bubble" style="border-color: var(--accent-rose);">
            <div class="message-content" style="color: #fca5a5;">
                <p><b>Ocurrió un problema:</b></p>
                <p>${escapeHtml(errorText)}</p>
                <p style="font-size: 0.8rem; color: var(--text-muted);">Puedes cambiar al <b>Motor Local Offline (100% Gratis)</b> en Configuración para consultar los reglamentos sin depender de APIs.</p>
            </div>
        </div>
    `;
    Elements.chatHistory.appendChild(row);
    scrollToBottom();
}

// ==========================================================================
// Assistant Interactive Features (Speech, TTS, Copy, Sources)
// ==========================================================================
function toggleSourcesDrawer(btn) {
    const content = btn.nextElementSibling;
    const arrow = btn.querySelector(".toggle-arrow");
    if (content.style.display === "none") {
        content.style.display = "flex";
        arrow.textContent = "▲";
    } else {
        content.style.display = "none";
        arrow.textContent = "▼";
    }
}

function askSuggestedQuestion(text) {
    Elements.chatInput.value = text;
    handleSendMessage();
}

function copyMessageText(msgId) {
    const bubble = document.getElementById(msgId);
    if (!bubble) return;
    const content = bubble.querySelector(".message-content").innerText;
    navigator.clipboard.writeText(content).then(() => {
        showToast("Texto copiado al portapapeles");
    });
}

function readAloudMessage(msgId) {
    const bubble = document.getElementById(msgId);
    if (!bubble) return;
    const content = bubble.querySelector(".message-content").innerText;

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel(); // Stop any previous speech
        const utterance = new SpeechSynthesisUtterance(content);
        utterance.lang = "es-MX";
        utterance.rate = 1.05;
        window.speechSynthesis.speak(utterance);
    } else {
        alert("La síntesis de voz no es compatible con tu navegador.");
    }
}

function toggleSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Tu navegador no soporta reconocimiento de voz. Te recomendamos usar Google Chrome o Microsoft Edge.");
        return;
    }

    if (AppState.isListening) {
        AppState.recognition.stop();
        AppState.isListening = false;
        Elements.btnMic.classList.remove("listening");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "es-MX";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        AppState.isListening = true;
        Elements.btnMic.classList.add("listening");
        Elements.chatInput.placeholder = "Escuchando tu pregunta para la UNACH...";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        Elements.chatInput.value = transcript;
        handleSendMessage();
    };

    recognition.onerror = (event) => {
        console.error("Speech error:", event.error);
        AppState.isListening = false;
        Elements.btnMic.classList.remove("listening");
        Elements.chatInput.placeholder = "Escribe tu pregunta sobre la UNACH...";
    };

    recognition.onend = () => {
        AppState.isListening = false;
        Elements.btnMic.classList.remove("listening");
        Elements.chatInput.placeholder = "Escribe tu pregunta sobre la UNACH...";
    };

    AppState.recognition = recognition;
    recognition.start();
}

// ==========================================================================
// Utilities
// ==========================================================================
function parseMarkdown(text) {
    if (!text) return "";

    // Escape basic HTML
    let out = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Headers
    out = out.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    out = out.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    out = out.replace(/^# (.*$)/gim, '<h2>$1</h2>');

    // Blockquotes
    out = out.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Bold & Italics
    out = out.replace(/\*\*\*(.*?)\*\*\*/gim, '<b><i>$1</i></b>');
    out = out.replace(/\*\*(.*?)\*\*/gim, '<b>$1</b>');
    out = out.replace(/\*(.*?)\*/gim, '<i>$1</i>');

    // Code blocks & inline code
    out = out.replace(/`([^`]+)`/gim, '<code>$1</code>');

    // Unordered lists
    out = out.replace(/^\s*[-*]\s+(.*$)/gim, '<li>$1</li>');
    out = out.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    out = out.replace(/<\/ul>\s*<ul>/gim, '');

    // Paragraphs & Linebreaks
    out = out.split(/\n\n+/).map(p => {
        p = p.trim();
        if (p.startsWith('<h') || p.startsWith('<blockquote') || p.startsWith('<ul') || p.startsWith('<ol')) {
            return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join("");

    return out;
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function scrollToBottom() {
    setTimeout(() => {
        Elements.chatHistory.scrollTop = Elements.chatHistory.scrollHeight;
    }, 50);
}

function removeElementById(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function openModal(modal) {
    if (!modal) return;
    modal.classList.add("active");
    modal.style.display = "flex";
}

function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove("active");
    modal.style.display = "none";
}

function openSettingsModal() {
    openModal(document.getElementById("settingsModal"));
}

function closeSettingsModal() {
    closeModal(document.getElementById("settingsModal"));
}

function openDocsModal() {
    openModal(document.getElementById("docsModal"));
}

function closeDocsModal() {
    closeModal(document.getElementById("docsModal"));
}

function toggleSidebar(forceState) {
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    if (!sidebar) return;

    if (window.innerWidth <= 900) {
        const isOpen = (typeof forceState === "boolean") ? forceState : !sidebar.classList.contains("open");
        sidebar.classList.toggle("open", isOpen);
        if (backdrop) {
            backdrop.classList.toggle("active", isOpen);
        }
        document.body.classList.toggle("sidebar-mobile-locked", isOpen);
    } else {
        const isCollapsed = (typeof forceState === "boolean") ? !forceState : !sidebar.classList.contains("collapsed");
        sidebar.classList.toggle("collapsed", isCollapsed);
    }
}

function closeSidebar() {
    toggleSidebar(false);
}

function showToast(message) {
    const toast = document.createElement("div");
    toast.style.position = "fixed";
    toast.style.bottom = "24px";
    toast.style.right = "24px";
    toast.style.background = "var(--unach-blue-700)";
    toast.style.color = "var(--unach-gold-300)";
    toast.style.border = "1px solid var(--unach-gold-400)";
    toast.style.padding = "10px 18px";
    toast.style.borderRadius = "10px";
    toast.style.fontSize = "0.85rem";
    toast.style.boxShadow = "var(--shadow-lg)";
    toast.style.zIndex = "999";
    toast.style.animation = "fadeIn 0.2s ease-out";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 2800);
}

// Expose globals for onclick handlers
window.toggleSourcesDrawer = toggleSourcesDrawer;
window.askSuggestedQuestion = askSuggestedQuestion;
window.copyMessageText = copyMessageText;
window.readAloudMessage = readAloudMessage;
window.openModal = openModal;
window.closeModal = closeModal;
window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;
window.openDocsModal = openDocsModal;
window.closeDocsModal = closeDocsModal;
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
