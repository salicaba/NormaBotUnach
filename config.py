import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "Reglamentos, Normas y Procedimientos de la UNACH"
DATA_DIR = BASE_DIR / "data"
CACHE_FILE = DATA_DIR / "unach_knowledge_base.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Load local .env if present (ignored by git for security)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Application Settings
SECRET_KEY = os.environ.get("SECRET_KEY", "unach_ai_secret_key_2026")
PORT = int(os.environ.get("PORT", 5000))
HOST = os.environ.get("HOST", "127.0.0.1")
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")

# AI Engine Defaults
DEFAULT_MODE = "gemini"  # "gemini" or "local_offline"
DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"
FALLBACK_GEMINI_MODELS = ["gemini-flash-lite-latest", "gemini-3-flash-preview", "gemini-3.8-flash"]

# Administration & Document Upload Settings
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "unach2026")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".png", ".jpg", ".jpeg"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max

# Categorization for UNACH Documents
DOCUMENT_CATEGORIES = {
    "alumnos_derechos": [
        "Estatuto-Integral",
        "LEY_ORGANICA",
        "Protocolo-de-actuacion",
        "Plan-Institucional-para-la-Cultura-de-Paz",
        "Lineamientos-ticos-para-el-uso-responsable-de-la-IA"
    ],
    "servicio_social": [
        "Reglamento-del-Servicio-Social",
        "Reglamento-de-Servicio-Social-para-la-Licenciatura-en-Mdico-Cirujano",
        "ACUERDO-CREACION-LINEAMIENTOS-PARA-IMPLEMENTACION-PROGRAMA-DE-ESTANCIAS"
    ],
    "academico_facultades": [
        "Reglamento-Interno-de-la-Facultad-de-Medicina",
        "Benemerita_UNACH_MODELO-EDUCATIVO",
        "MODELO-ACADeMICO",
        "Reglamento-CEDUCAD",
        "Reglamento-General-de-Academias",
        "Reglamento-para-la-Planeacion-Academica"
    ],
    "normatividad_tribunal": [
        "tribunal-universitario",
        "5RegGral_ComMixtaPerm",
        "LINEAMIENTOS-DE-SEGURIDAD",
        "normas_que_regulan"
    ],
    "formatos_administrativos": [
        "Anexo",
        "Acta Entrega",
        "Instructivos de llenado",
        "formato_normas",
        "Guia_er_unach",
        "MOF-DAC",
        "manual_tecnico"
    ]
}
