import os
from flask import Blueprint, jsonify, request

def create_settings_blueprint(ai_engine):
    settings_bp = Blueprint("settings", __name__)

    @settings_bp.route("/api/settings", methods=["GET"])
    def get_settings():
        """Returns current engine configurations (with masked API key)."""
        s = ai_engine.settings
        raw_key = s.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        masked_key = ""
        if raw_key:
            if len(raw_key) > 8:
                masked_key = raw_key[:4] + "..." + raw_key[-4:]
            else:
                masked_key = "****"

        return jsonify({
            "mode": ai_engine.get_active_mode(),
            "configured_mode": s.get("mode", "gemini"),
            "has_gemini_key": bool(raw_key),
            "masked_key": masked_key,
            "model_name": s.get("model_name", "gemini-2.5-flash"),
            "available_modes": [
                {
                    "id": "gemini",
                    "name": "Google Gemini 2.5 Flash",
                    "description": "100% Gratis con clave de Google AI Studio. Respuestas naturales, empáticas y detalladas.",
                    "requires_key": True
                },
                {
                    "id": "local_offline",
                    "name": "Motor Local Offline (Sin Clave)",
                    "description": "100% Gratis y 100% Offline. No requiere internet ni registros. Extrae y resume normatividad directamente.",
                    "requires_key": False
                }
            ]
        })

    @settings_bp.route("/api/settings", methods=["POST"])
    def update_settings():
        """Updates API key and preferences."""
        data = request.get_json() or {}
        new_mode = data.get("mode")
        api_key = data.get("gemini_api_key")
        model_name = data.get("model_name")

        updates = {}
        if new_mode in ["gemini", "local_offline"]:
            updates["mode"] = new_mode

        if api_key is not None:
            clean_key = api_key.strip()
            # If user sent blank and wants to clear, allow clearing
            updates["gemini_api_key"] = clean_key
            if clean_key:
                os.environ["GEMINI_API_KEY"] = clean_key

        if model_name:
            updates["model_name"] = model_name

        ai_engine.save_settings(updates)

        return jsonify({
            "message": "Configuración guardada exitosamente.",
            "mode": ai_engine.get_active_mode(),
            "has_gemini_key": bool(ai_engine.settings.get("gemini_api_key"))
        })

    @settings_bp.route("/api/settings/test", methods=["POST"])
    def test_gemini_connection():
        """Verifies if the configured or provided Gemini API key works."""
        data = request.get_json() or {}
        test_key = data.get("gemini_api_key", "").strip() or ai_engine.settings.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()

        if not test_key:
            return jsonify({
                "success": False,
                "error": "No se proporcionó ninguna clave API de Gemini."
            }), 400

        try:
            import requests
            import config
            
            # Test with working models
            success = False
            last_err = ""
            for model_to_test in config.FALLBACK_GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_to_test}:generateContent?key={test_key}"
                payload = {
                    "contents": [{"parts": [{"text": "Hola, responde sólo: 'UNACH Conexión Exitosa'"}]}]
                }
                try:
                    resp = requests.post(url, json=payload, timeout=12)
                    if resp.status_code == 200:
                        success = True
                        ai_engine.settings["model_name"] = model_to_test
                        ai_engine.save_settings({"model_name": model_to_test})
                        break
                    else:
                        last_err = f"Código {resp.status_code}: {resp.text}"
                except Exception as req_e:
                    last_err = str(req_e)

            if success:
                return jsonify({
                    "success": True,
                    "message": "¡Clave de Google Gemini validada correctamente! La conexión con la IA de la UNACH es 100% operativa."
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Error de autenticación o conexión: {last_err}"
                }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error de conexión: {str(e)}"
            }), 500

    return settings_bp
