/**
 * API Service for UNACH AI Assistant
 * Interacts with Backend Controllers
 */
const API = {
    /**
     * Send student question to chat controller
     */
    async askQuestion(query, category = "all", mode = null) {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, category, mode })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || `Error ${response.status}: Error al procesar la consulta.`);
        }
        return await response.json();
    },

    /**
     * Fetch document catalog and statistics
     */
    async getDocuments() {
        const response = await fetch("/api/documents");
        if (!response.ok) {
            throw new Error("No se pudo obtener el catálogo de documentos.");
        }
        return await response.json();
    },

    /**
     * Trigger re-indexing of documents
     */
    async reindex() {
        const response = await fetch("/api/reindex", { method: "POST" });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || "Fallo en la re-indexación.");
        }
        return await response.json();
    },

    /**
     * Fetch current settings (API key status, active mode)
     */
    async getSettings() {
        const response = await fetch("/api/settings");
        if (!response.ok) {
            throw new Error("No se pudo obtener la configuración.");
        }
        return await response.json();
    },

    /**
     * Save new settings
     */
    async updateSettings(settings) {
        const response = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || "No se pudo actualizar la configuración.");
        }
        return await response.json();
    },

    /**
     * Test Gemini API Key
     */
    async testConnection(gemini_api_key) {
        const response = await fetch("/api/settings/test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gemini_api_key })
        });
        return await response.json();
    },

    /**
     * Admin login authentication
     */
    async adminLogin(password) {
        const response = await fetch("/api/admin/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password })
        });
        return await response.json();
    },

    /**
     * Admin upload files with auto-indexing
     */
    async adminUpload(formData, password) {
        const response = await fetch("/api/admin/upload", {
            method: "POST",
            headers: { "X-Admin-Password": password },
            body: formData
        });
        return await response.json();
    },

    /**
     * Admin delete document and auto-reindex
     */
    async adminDelete(filename, password) {
        const response = await fetch(`/api/admin/documents/${encodeURIComponent(filename)}`, {
            method: "DELETE",
            headers: { "X-Admin-Password": password }
        });
        return await response.json();
    }
};

window.API = API;
