from flask import Blueprint, jsonify, request
from pathlib import Path

def create_document_blueprint(knowledge_base):
    doc_bp = Blueprint("document", __name__)

    @doc_bp.route("/api/documents", methods=["GET"])
    def list_documents():
        """Returns indexed documents with summary statistics."""
        docs = knowledge_base.get_documents_list()
        
        # Aggregate statistics
        total_docs = len(docs)
        total_chunks = len(knowledge_base.chunks)
        total_pages = sum(d.get("total_pages", 0) for d in docs)
        
        categories = {}
        for d in docs:
            cat = d.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1

        return jsonify({
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "total_pages": total_pages,
            "categories": categories,
            "documents": docs
        })

    @doc_bp.route("/api/documents/<filename>/preview", methods=["GET"])
    def preview_document(filename):
        """Returns chunks and metadata for a specific document."""
        chunks = [c for c in knowledge_base.chunks if c.get("document") == filename]
        doc_info = knowledge_base.documents.get(filename)

        if not chunks and not doc_info:
            return jsonify({"error": "Documento no encontrado en el índice."}), 404

        return jsonify({
            "filename": filename,
            "info": doc_info,
            "chunk_count": len(chunks),
            "preview_chunks": chunks[:10]  # First 10 chunks for fast inspection
        })

    @doc_bp.route("/api/admin/login", methods=["POST"])
    def admin_login():
        """Authenticates administrator/creator."""
        import config
        data = request.get_json() or {}
        password = data.get("password", "")
        if password == config.ADMIN_PASSWORD:
            return jsonify({"success": True, "message": "Acceso concedido."})
        return jsonify({"success": False, "error": "Contraseña incorrecta."}), 401

    @doc_bp.route("/api/admin/upload", methods=["POST"])
    def admin_upload_documents():
        """Uploads one or more documents and automatically indexes them."""
        import config
        from werkzeug.utils import secure_filename
        
        # Verify admin password header or form
        auth_pass = request.headers.get("X-Admin-Password") or request.form.get("password")
        if auth_pass != config.ADMIN_PASSWORD:
            return jsonify({"error": "No autorizado para subir documentos."}), 403

        if "files" not in request.files and "file" not in request.files:
            return jsonify({"error": "No se recibieron archivos."}), 400

        files = request.files.getlist("files") if "files" in request.files else [request.files["file"]]
        saved_files = []

        config.DOCS_DIR.mkdir(parents=True, exist_ok=True)

        for file in files:
            if not file or not file.filename:
                continue
            filename = secure_filename(file.filename)
            ext = Path(filename).suffix.lower()
            if ext not in config.ALLOWED_EXTENSIONS:
                continue
            
            dest_path = config.DOCS_DIR / filename
            file.save(str(dest_path))
            saved_files.append(filename)

        if not saved_files:
            return jsonify({"error": "Ningún archivo válido fue subido. Formatos permitidos: PDF, Word, Excel, TXT, Imágenes."}), 400

        # Automatically rebuild index
        try:
            stats = knowledge_base.build_index()
            return jsonify({
                "success": True,
                "message": f"Se subieron e indexaron {len(saved_files)} archivo(s) correctamente.",
                "uploaded_files": saved_files,
                "total_documents": stats.get("total_documents", 0),
                "total_chunks": stats.get("total_chunks", 0)
            })
        except Exception as e:
            return jsonify({
                "success": True,
                "warning": f"Archivos guardados pero ocurrió un error al indexar: {str(e)}",
                "uploaded_files": saved_files
            })

    @doc_bp.route("/api/admin/documents/<filename>", methods=["DELETE"])
    def admin_delete_document(filename):
        """Deletes a document from the official folder and re-indexes."""
        import config
        from werkzeug.utils import secure_filename
        
        auth_pass = request.headers.get("X-Admin-Password")
        if auth_pass != config.ADMIN_PASSWORD:
            return jsonify({"error": "No autorizado para eliminar documentos."}), 403

        safe_name = secure_filename(filename)
        target_file = config.DOCS_DIR / safe_name
        
        if not target_file.exists():
            return jsonify({"error": "El archivo no existe en el servidor."}), 404

        try:
            target_file.unlink()
            stats = knowledge_base.build_index()
            return jsonify({
                "success": True,
                "message": f"Documento '{safe_name}' eliminado e índice actualizado.",
                "total_documents": stats.get("total_documents", 0),
                "total_chunks": stats.get("total_chunks", 0)
            })
        except Exception as e:
            return jsonify({"error": f"Error al eliminar: {str(e)}"}), 500

    @doc_bp.route("/api/reindex", methods=["POST"])
    def reindex_all():
        """Triggers document re-indexing."""
        try:
            stats = knowledge_base.build_index()
            return jsonify({
                "message": "Indexación completada con éxito.",
                "total_documents": stats.get("total_documents", 0),
                "total_chunks": stats.get("total_chunks", 0)
            })
        except Exception as e:
            return jsonify({
                "error": f"Error durante la indexación: {str(e)}"
            }), 500

    return doc_bp
