import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import config

class AIEngine:
    """
    Dual-mode AI Engine for UNACH Question Answering:
    1. Google Gemini Flash (100% Free API Tier via Google AI Studio)
    2. Local Extractive & Synthesizing Engine (100% Free, Offline, Zero API Key required)
    """

    SYSTEM_PROMPT = """Eres el Asistente Virtual Oficial de Reglamentos y Normatividad de la Universidad Autónoma de Chiapas (UNACH).
Tu misión es orientar y resolver dudas de los alumnos y la comunidad universitaria con base EXCLUSIVA en los reglamentos, estatutos, lineamientos y procedimientos oficiales proporcionados en el contexto.

Directrices Obligatorias:
1. Responde de forma clara, profesional, empática y orientada al estudiante universitario.
2. CITA SIEMPRE la fuente exacta: Menciona el nombre del documento (ej. Reglamento del Servicio Social, Estatuto Integral, Lineamientos de IA) y el número de Artículo o Sección correspondiente.
3. Si la respuesta contiene requisitos, plazos, pasos o sanciones, preséntalos en listas estructuradas con viñetas claras y legibles.
4. Si la información solicitada no se encuentra en los fragmentos provistos, aclara amablemente que en los documentos indexados no se localiza ese punto específico y sugiere a qué área o coordinación de la UNACH acudir.
5. NO inventes normas, fechas o artículos que no aparezcan en las fuentes.
"""

    def __init__(self, settings_file: Path = config.SETTINGS_FILE):
        self.settings_file = Path(settings_file)
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Loads persistent user settings like API key and mode."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[AIEngine] Error reading settings: {e}")

        # Defaults
        return {
            "mode": config.DEFAULT_MODE,  # "gemini" or "local_offline"
            "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
            "model_name": config.DEFAULT_GEMINI_MODEL
        }

    def save_settings(self, new_settings: Dict[str, Any]):
        """Updates and persists settings."""
        self.settings.update(new_settings)
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AIEngine] Error saving settings: {e}")

    def get_active_mode(self) -> str:
        """Determines active mode: fallback to local_offline if gemini has no key."""
        mode = self.settings.get("mode", "gemini")
        api_key = self.settings.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        if mode == "gemini" and not api_key:
            return "local_offline"
        return mode

    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], mode_override: Optional[str] = None) -> Dict[str, Any]:
        """Generates answer using active engine (Gemini or Local Offline)."""
        mode = mode_override or self.get_active_mode()

        if mode == "gemini":
            try:
                return self._generate_with_gemini(query, context_chunks)
            except Exception as e:
                print(f"[AIEngine] Gemini call failed: {e}. Falling back to Local Offline Engine.")
                res = self._generate_with_local(query, context_chunks)
                res["fallback_triggered"] = True
                res["fallback_reason"] = str(e)
                return res
        else:
            return self._generate_with_local(query, context_chunks)

    def _generate_with_gemini(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calls Google Gemini API (Free tier from Google AI Studio)."""
        api_key = self.settings.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("No se ha configurado la clave API de Gemini. Puedes usar el Modo Local Gratuito o agregar tu clave gratis.")

        # Build context block
        context_text = ""
        for idx, chunk in enumerate(context_chunks):
            doc = chunk.get("document", "Documento UNACH")
            page = chunk.get("page", 1)
            art = chunk.get("article_ref", "")
            content = chunk.get("content", "")
            context_text += f"\n--- FUENTE {idx+1}: [{doc} | Pág. {page} | {art}] ---\n{content}\n"

        prompt = f"""{self.SYSTEM_PROMPT}

A continuación tienes los fragmentos oficiales extraídos de los documentos normativos de la UNACH:
{context_text}

PREGUNTA DEL ALUMNO O USUARIO:
{query}

Por favor elabora una respuesta completa, fidedigna, bien explicada en formato Markdown, citando los artículos y documentos correspondientes. Si hay pasos a seguir, organízalos claramente."""

        # Try available working models
        configured_model = self.settings.get("model_name", config.DEFAULT_GEMINI_MODEL)
        candidate_models = [configured_model] + [m for m in config.FALLBACK_GEMINI_MODELS if m != configured_model]

        last_error = None
        for model_name in candidate_models:
            try:
                # Direct REST API
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    # Remember working model
                    if model_name != configured_model:
                        self.settings["model_name"] = model_name
                        self.save_settings({"model_name": model_name})
                    return {
                        "answer": answer_text,
                        "engine": "gemini",
                        "model": model_name,
                        "sources": self._format_sources(context_chunks)
                    }
                else:
                    last_error = f"Error {resp.status_code}: {resp.text}"
            except Exception as e:
                last_error = str(e)

        raise RuntimeError(f"No fue posible conectar con los modelos de Gemini: {last_error}")

    def _generate_with_local(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Local Offline Synthesizer: 100% Free, runs entirely on CPU without any cloud or API key.
        Extracts relevant articles, highlights matching clauses, and structures student guidance cleanly.
        """
        if not context_chunks:
            return {
                "answer": "No se encontraron artículos o reglamentos que coincidan exactamente con tu consulta en los documentos disponibles. Te sugerimos revisar las palabras clave o consultar el índice de reglamentos.",
                "engine": "local_offline",
                "model": "Motor Semántico Local UNACH (Offline)",
                "sources": []
            }

        lines = []
        lines.append("### 📚 Información Oficial de la Legislación UNACH\n")
        lines.append(f"Para orientarte sobre tu consulta: **«{query}»**, la normatividad de la Universidad Autónoma de Chiapas establece lo siguiente:\n")

        # Top relevant article focus
        main_chunk = context_chunks[0]
        main_doc = main_chunk.get("document_title", "Documento Oficial")
        main_ref = main_chunk.get("article_ref", "Disposición Oficial")

        lines.append(f"#### 📌 Disposición Principal: {main_doc} ({main_ref})")
        lines.append(f"> 📄 **Fuente:** `{main_chunk.get('document', '')}` • Página {main_chunk.get('page', 1)}\n")

        # Format main chunk cleanly without chopping sentences
        clean_main = main_chunk.get("content", "").strip()
        # Remove repeated header if present
        clean_main = re.sub(r'^[^\n]+-\s*', '', clean_main)
        lines.append(f"{clean_main}\n")

        # Additional complementary references if found
        if len(context_chunks) > 1:
            lines.append("---")
            lines.append("#### 📋 Artículos y Disposiciones Complementarias Relacionadas:\n")
            for idx, chunk in enumerate(context_chunks[1:3], 1):
                doc_title = chunk.get("document_title", chunk.get("document", "Documento"))
                art = chunk.get("article_ref", "")
                page = chunk.get("page", 1)
                content = chunk.get("content", "").strip()
                content = re.sub(r'^[^\n]+-\s*', '', content)

                lines.append(f"**{idx}. {doc_title}** — *{art}* (Pág. {page})")
                # Show first 400 clean characters or first paragraph
                first_para = content.split("\n\n")[0] if "\n\n" in content else content[:400]
                lines.append(f"> {first_para}\n")

        lines.append("---")
        lines.append("💡 **Nota:** Estás usando el **Motor Local Offline** (búsqueda de fragmentos y artículos exactos en tu equipo). Si deseas que una IA te redacte y explique la respuesta conversacionalmente paso a paso como un tutor, puedes activar **Google Gemini Flash (100% Gratis)** en el botón de **Configuración (⚙️)** con una clave gratuita de Google AI Studio.")

        return {
            "answer": "\n".join(lines),
            "engine": "local_offline",
            "model": "Motor Semántico Local UNACH (Offline)",
            "sources": self._format_sources(context_chunks)
        }

    def _format_sources(self, context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formats sources for presentation in the View layer."""
        sources = []
        seen = set()

        for chunk in context_chunks:
            key = (chunk.get("document"), chunk.get("page"), chunk.get("article_ref"))
            if key in seen:
                continue
            seen.add(key)

            sources.append({
                "document": chunk.get("document"),
                "document_title": chunk.get("document_title"),
                "category": chunk.get("category", "general"),
                "page": chunk.get("page"),
                "sheet": chunk.get("sheet", ""),
                "header": chunk.get("header", ""),
                "article_ref": chunk.get("article_ref", ""),
                "snippet": chunk.get("content", "")[:280] + ("..." if len(chunk.get("content", "")) > 280 else ""),
                "score": chunk.get("score", 0)
            })

        return sources
