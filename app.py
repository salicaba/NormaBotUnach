import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

import config
from models.knowledge_base import KnowledgeBase
from models.ai_engine import AIEngine
from controllers.chat_controller import create_chat_blueprint
from controllers.document_controller import create_document_blueprint
from controllers.settings_controller import create_settings_blueprint

def create_app():
    """Application Factory assembling the Model-View-Controller (MVC) architecture."""
    
    # Configure Flask with explicit template and static folders in View layer
    app = Flask(
        __name__,
        template_folder=str(config.BASE_DIR / "views" / "templates"),
        static_folder=str(config.BASE_DIR / "views" / "static")
    )
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.secret_key = config.SECRET_KEY
    CORS(app)

    @app.after_request
    def add_header(response):
        """Disables browser caching so frontend changes are immediately visible."""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # 1. MODEL INITIALIZATION
    print("[UNACH AI] Cargando el Modelo (Base de Conocimiento y Motor IA)...")
    knowledge_base = KnowledgeBase()
    ai_engine = AIEngine()

    # 2. CONTROLLERS REGISTRATION
    print("[UNACH AI] Registrando Controladores...")
    chat_bp = create_chat_blueprint(knowledge_base, ai_engine)
    doc_bp = create_document_blueprint(knowledge_base)
    settings_bp = create_settings_blueprint(ai_engine)

    app.register_blueprint(chat_bp)
    app.register_blueprint(doc_bp)
    app.register_blueprint(settings_bp)

    # 3. VIEW ROUTES
    @app.route("/")
    def index():
        """Serves the main UNACH AI Portal View for students."""
        return render_template("index.html")

    @app.route("/admin")
    def admin():
        """Serves the UNACH AI Creator / Administration Portal."""
        return render_template("admin.html")

    @app.route("/static/<path:filename>")
    def serve_static(filename):
        """Serves static files (CSS, JS, assets)."""
        return send_from_directory(app.static_folder, filename)

    return app, knowledge_base

# Main Entry Point
if __name__ == "__main__":
    app, kb = create_app()
    port = config.PORT
    host = config.HOST
    print("\n" + "="*60)
    print("🐆  UNACH NORMA-BOT - ASISTENTE DE REGLAMENTOS PARA ALUMNOS")
    print("="*60)
    print(f"📍 Servidor ejecutándose en: http://{host}:{port}")
    print(f"📚 Documentos cargados: {len(kb.documents)} archivos")
    print(f"📑 Artículos y fragmentos: {len(kb.chunks)} indexados")
    print("💎 100% Gratuito (Modo Gemini Flash + Modo Local Offline)")
    print("="*60 + "\n")
    app.run(host=host, port=port, debug=config.DEBUG)
