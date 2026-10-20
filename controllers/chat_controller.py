import time
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify

def create_chat_blueprint(knowledge_base, ai_engine):
    chat_bp = Blueprint("chat", __name__)

    @chat_bp.route("/api/chat", methods=["POST"])
    def chat_endpoint():
        """Handles question asking, retrieval, and AI generation."""
        start_time = time.time()
        data = request.get_json() or {}

        query = data.get("query", "").strip()
        category = data.get("category", "all")
        mode = data.get("mode")  # None, "gemini", or "local_offline"

        if not query:
            return jsonify({"error": "Por favor escribe una pregunta o consulta."}), 400

        # Step 1: Retrieve context from KnowledgeBase (Model)
        chunks = knowledge_base.search(query=query, top_k=5, category=category)

        # Step 2: Generate response using AI Engine (Model)
        try:
            result = ai_engine.generate_response(query=query, context_chunks=chunks, mode_override=mode)
        except Exception as e:
            return jsonify({
                "error": f"Error al generar la respuesta: {str(e)}"
            }), 500

        elapsed_ms = round((time.time() - start_time) * 1000)

        # Step 3: Compute contextual suggested questions
        suggestions = generate_suggestions(query, chunks)

        return jsonify({
            "query": query,
            "answer": result.get("answer", ""),
            "engine": result.get("engine", "local_offline"),
            "model": result.get("model", ""),
            "sources": result.get("sources", []),
            "elapsed_ms": elapsed_ms,
            "suggestions": suggestions,
            "fallback_triggered": result.get("fallback_triggered", False),
            "fallback_reason": result.get("fallback_reason")
        })

    def generate_suggestions(query: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """Provides relevant next question suggestions for students."""
        q_lower = query.lower()
        if "servicio social" in q_lower:
            return [
                "¿Cuántas horas de servicio social debo cumplir?",
                "¿Cuáles son los motivos de cancelación o suspensión del servicio social?",
                "¿Qué requisitos necesito para tramitar la carta de liberación?"
            ]
        elif "ia" in q_lower or "inteligencia artificial" in q_lower:
            return [
                "¿En qué casos está permitido usar IA en mis tareas o proyectos?",
                "¿Cuáles son las sanciones por usar IA sin citar las fuentes?",
                "¿Qué responsabilidades tienen los profesores frente al uso de IA?"
            ]
        elif "derecho" in q_lower or "estatuto" in q_lower or "alumno" in q_lower:
            return [
                "¿Cuáles son mis derechos fundamentales como alumno de la UNACH?",
                "¿Qué causas ameritan una sanción o baja temporal según el Estatuto?",
                "¿Cómo puedo acudir al Tribunal Universitario si vulneran mis derechos?"
            ]
        elif "medicina" in q_lower or "médico" in q_lower:
            return [
                "¿Cómo se asignan las plazas de internado y servicio social en Medicina?",
                "¿Qué faltas disciplinarias contempla el reglamento de la Facultad de Medicina?",
                "¿Cuáles son los requisitos de acreditación de asignaturas clínicas?"
            ]
        elif chunks:
            # Derive from retrieved document title
            first_doc = chunks[0].get("document_title", "")
            return [
                f"¿Qué dice el artículo siguiente en {first_doc}?",
                "¿Cuáles son los requisitos y plazos que marca este reglamento?",
                "¿Qué trámites específicos debo realizar como estudiante?"
            ]
        return [
            "¿Cuáles son los requisitos de Servicio Social en la UNACH?",
            "¿Qué derechos tengo como alumno en el Estatuto Integral?",
            "¿Cuáles son los lineamientos para el uso de Inteligencia Artificial?"
        ]

    return chat_bp
