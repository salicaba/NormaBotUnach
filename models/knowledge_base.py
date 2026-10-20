import os
import sys
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import config
from models.document_parser import DocumentParser
from models.chunker import SmartChunker

# Spanish stop words for clean token matching
SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o",
    "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "tambien",
    "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos",
    "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mi",
    "antes", "algunos", "que", "unos", "yo", "otro", "otras", "otra", "el", "tanto", "esa"
}

def normalize_text(text: str) -> str:
    """Removes accents, converts to lowercase, strips unwanted characters."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join(text.split())

def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Tokenizes normalized text."""
    normalized = normalize_text(text)
    tokens = normalized.split()
    if remove_stopwords:
        tokens = [t for t in tokens if len(t) > 1 and t not in SPANISH_STOPWORDS]
    return tokens


class KnowledgeBase:
    """
    Manages document catalog, chunks, and hybrid BM25 retrieval for UNACH documentation.
    """

    def __init__(self, docs_dir: Path = config.DOCS_DIR, cache_file: Path = config.CACHE_FILE, enable_ocr: bool = False):
        self.docs_dir = Path(docs_dir)
        self.cache_file = Path(cache_file)
        self.parser = DocumentParser(enable_ocr=enable_ocr)
        self.chunker = SmartChunker(target_chunk_size=750, overlap=120)

        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Dict[str, Any]] = []
        self.term_doc_freq: Dict[str, int] = {}
        self.avg_chunk_len: float = 0.0

        # Load from cache if exists
        self.load_or_index()

    def categorize_filename(self, filename: str) -> str:
        """Determines category based on config mapping."""
        for category, patterns in config.DOCUMENT_CATEGORIES.items():
            for pattern in patterns:
                if pattern.lower() in filename.lower():
                    return category
        return "general"

    def load_or_index(self, force_reindex: bool = False):
        """Loads from precomputed JSON cache or builds index."""
        if not force_reindex and self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", {})
                    self.chunks = data.get("chunks", [])
                    print(f"[KnowledgeBase] Loaded {len(self.chunks)} chunks across {len(self.documents)} documents from cache.", flush=True)
                    self._build_bm25_stats()
                    return
            except Exception as e:
                print(f"[KnowledgeBase] Cache read failed ({e}), rebuilding index...", flush=True)

        self.build_index()

    def build_index(self, progress_callback=None) -> Dict[str, Any]:
        """Scans docs folder, parses, chunks, and saves index."""
        print(f"[KnowledgeBase] Starting indexing from {self.docs_dir}...", flush=True)
        all_files = sorted(list(self.docs_dir.glob("*.*")))
        supported_exts = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".csv", ".png", ".jpg", ".jpeg"}
        target_files = [f for f in all_files if f.suffix.lower() in supported_exts]

        self.documents = {}
        self.chunks = []

        total_files = len(target_files)
        for idx, file_path in enumerate(target_files):
            filename = file_path.name
            category = self.categorize_filename(filename)

            if progress_callback:
                progress_callback(idx + 1, total_files, filename)
            print(f"[{idx+1}/{total_files}] Indexing {filename} ({category})...", flush=True)

            parsed = self.parser.parse_file(file_path)
            if not parsed or not parsed.get("has_text"):
                continue

            doc_chunks = self.chunker.chunk_document(parsed, category=category)
            self.chunks.extend(doc_chunks)

            self.documents[filename] = {
                "filename": filename,
                "title": parsed["filename"].rsplit(".", 1)[0].replace("-", " ").replace("_", " "),
                "format": parsed["format"],
                "total_pages": parsed["total_pages"],
                "total_chunks": len(doc_chunks),
                "category": category,
                "size_bytes": file_path.stat().st_size
            }

        self._build_bm25_stats()
        self.save_cache()

        print(f"[KnowledgeBase] Indexing complete: {len(self.chunks)} chunks from {len(self.documents)} documents.")
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks)
        }

    def _build_bm25_stats(self):
        """Computes BM25 frequencies and average lengths for ranking."""
        self.term_doc_freq = {}
        total_len = 0

        for chunk in self.chunks:
            tokens = set(tokenize(chunk.get("content", "")))
            total_len += len(chunk.get("content", "").split())
            for token in tokens:
                self.term_doc_freq[token] = self.term_doc_freq.get(token, 0) + 1

        num_chunks = len(self.chunks) or 1
        self.avg_chunk_len = total_len / num_chunks

    def save_cache(self):
        """Saves documents and chunks to JSON cache."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "documents": self.documents,
                    "chunks": self.chunks
                }, f, ensure_ascii=False, indent=2)
            print(f"[KnowledgeBase] Cache saved to {self.cache_file}")
        except Exception as e:
            print(f"[KnowledgeBase] Error saving cache: {e}")

    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Hybrid BM25 and keyword search over indexed chunks.
        Applies article boosting, filename affinity, and exact phrase matching.
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Student-focused document priorities
        norm_query = normalize_text(query)
        num_chunks = len(self.chunks)

        # Detect intent and document affinity
        has_estatuto = "estatuto" in norm_query
        has_servicio_social = "servicio social" in norm_query or "servicio" in norm_query
        has_ia = "inteligencia artificial" in norm_query or re.search(r'\bia\b', norm_query) is not None
        has_medicina = "medicina" in norm_query or "medico" in norm_query
        has_violencia = "violencia" in norm_query or "acoso" in norm_query or "genero" in norm_query
        has_tribunal = "tribunal" in norm_query or "queja" in norm_query
        has_baja = "baja" in norm_query or "sancion" in norm_query or "falta" in norm_query

        # Check if user specifically asked for admin formats/guides
        is_asking_for_format = any(w in norm_query for w in ["formato", "anexo", "acta", "entrega recepcion", "instructivo", "mof", "manual"])

        # Detect article number query (e.g. "artículo 15" -> "15")
        art_match = re.search(r'(?:articulo|art)\s*(\d+)', norm_query)
        target_art_num = art_match.group(1) if art_match else None

        # BM25 constants
        k1 = 1.5
        b = 0.75

        scored_chunks = []

        for chunk in self.chunks:
            # Category filter
            if category and category != "all" and chunk.get("category") != category:
                continue

            doc_name = chunk.get("document", "")
            doc_norm = normalize_text(doc_name)
            content = chunk.get("content", "")
            norm_content = normalize_text(content)
            content_tokens = norm_content.split()
            chunk_len = len(content_tokens)

            # Frequency of query tokens in chunk
            term_counts = {}
            for t in content_tokens:
                if t in query_tokens:
                    term_counts[t] = term_counts.get(t, 0) + 1

            bm25_score = 0.0
            matched_terms = 0

            for q_term in query_tokens:
                freq = term_counts.get(q_term, 0)
                if freq > 0:
                    matched_terms += 1
                    df = self.term_doc_freq.get(q_term, 1)
                    idf = math.log(1.0 + (num_chunks - df + 0.5) / (df + 0.5))
                    denom = freq + k1 * (1.0 - b + b * (chunk_len / (self.avg_chunk_len or 1.0)))
                    bm25_score += idf * ((freq * (k1 + 1.0)) / (denom or 1.0))

            if matched_terms == 0:
                continue

            score = bm25_score

            # Coverage boost: rewarding chunks that contain more query terms
            term_coverage = matched_terms / len(query_tokens)
            score *= (1.0 + term_coverage * 2.0)

            # Exact phrase boost
            if len(query.strip()) > 8 and norm_query in norm_content:
                score += 15.0

            # Subphrase boosts for key phrases
            for key_phrase in ["baja temporal", "baja definitiva", "servicio social", "derechos de los alumnos", "inteligencia artificial", "tribunal universitario"]:
                if key_phrase in norm_query and key_phrase in norm_content:
                    score += 25.0

            # Article boost
            if target_art_num:
                norm_art = normalize_text(chunk.get("article_ref", ""))
                if f"articulo {target_art_num}" in norm_art or f"art {target_art_num}" in norm_art:
                    score += 35.0

            # Explicit document name matching boosts
            if has_estatuto and "estatuto" in doc_norm:
                score += 30.0
            if has_servicio_social and "servicio social" in doc_norm:
                score += 30.0
            if has_ia and ("ia" in doc_norm or "inteligencia" in doc_norm):
                score += 35.0
            if has_medicina and "medicina" in doc_norm:
                score += 30.0
            if has_violencia and ("violencia" in doc_norm or "protocolo" in doc_norm):
                score += 30.0
            if has_tribunal and "tribunal" in doc_norm:
                score += 30.0

            # If user asks about student sanctions/bajas, prioritize Estatuto Integral
            if has_baja and "estatuto" in doc_norm:
                score += 20.0

            # Demote administrative handover formats when not asked for
            if not is_asking_for_format:
                is_admin_format = any(w in doc_norm for w in ["anexo", "instructivo", "acta entrega", "guia er", "mof dac", "manual tecnico"])
                if is_admin_format:
                    score *= 0.2  # Heavily penalize administrative HR handover docs for student queries

            scored_chunks.append({
                "score": round(score, 3),
                "document": chunk["document"],
                "document_title": chunk["document_title"],
                "category": chunk.get("category", "general"),
                "page": chunk["page"],
                "sheet": chunk.get("sheet", ""),
                "header": chunk.get("header", ""),
                "article_ref": chunk.get("article_ref", ""),
                "content": content
            })

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def get_documents_list(self) -> List[Dict[str, Any]]:
        """Returns metadata list of all indexed documents."""
        return list(self.documents.values())
