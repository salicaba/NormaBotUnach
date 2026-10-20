import os
import config
from app import create_app

# WSGI Entry Point for Production (Gunicorn / Render / Railway)
app, knowledge_base = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
