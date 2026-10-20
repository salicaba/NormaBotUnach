"""
UNACH AI - Standalone Indexer & Knowledge Base Builder
Permite indexar todos los reglamentos, acuerdos, normas y procedimientos
almacenados en la carpeta "Reglamentos, Normas y Procedimientos de la UNACH".

Uso:
    python indexer.py                 # Indexa todos los documentos
    python indexer.py --reindex       # Fuerza la re-indexación completa
    python indexer.py --search "..."  # Prueba una búsqueda semántica
"""

import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from models.knowledge_base import KnowledgeBase
import config

def main():
    parser = argparse.ArgumentParser(description="UNACH Document Indexer (Modelo de Conocimiento)")
    parser.add_argument("--reindex", action="store_true", help="Fuerza la re-indexación de todos los archivos")
    parser.add_argument("--search", type=str, help="Prueba una consulta de búsqueda sobre el índice")
    parser.add_argument("--top", type=int, default=3, help="Número de resultados para la búsqueda")

    args = parser.parse_args()

    print("=" * 65)
    print("🐆  UNACH - CONSTRUCTOR DE BASE DE CONOCIMIENTO (INDEXADOR)")
    print("=" * 65)
    print(f"📁 Directorio de documentos: {config.DOCS_DIR}")
    print(f"💾 Archivo de caché: {config.CACHE_FILE}\n")

    kb = KnowledgeBase()

    if args.reindex:
        print("[*] Forzando re-indexación completa...")
        stats = kb.build_index()
        print(f"\n✅ Indexación finalizada:")
        print(f"   • Total de documentos procesados: {stats['total_documents']}")
        print(f"   • Total de fragmentos/artículos: {stats['total_chunks']}")

    if args.search:
        query = args.search
        print(f"\n🔍 Probando búsqueda para: «{query}»")
        results = kb.search(query=query, top_k=args.top)

        if not results:
            print("❌ No se encontraron resultados.")
        else:
            print(f"✨ Se encontraron {len(results)} fragmentos relevantes:\n")
            for idx, r in enumerate(results, 1):
                print(f"[{idx}] Puntaje: {r['score']} | Documento: {r['document_title']}")
                print(f"    Referencia: {r['article_ref']} (Pág. {r['page']})")
                print(f"    Extracto: {r['content'][:180]}...")
                print("-" * 60)

    if not args.reindex and not args.search:
        print(f"📊 Estado actual del índice:")
        print(f"   • Documentos registrados: {len(kb.documents)}")
        print(f"   • Artículos y fragmentos indexados: {len(kb.chunks)}")
        print(f"   • Ubicación de la base de datos: {config.CACHE_FILE}")
        print("\nPara probar una búsqueda ejecuta:")
        print('   python indexer.py --search "requisitos de servicio social"')
        print("Para forzar una re-indexación ejecuta:")
        print("   python indexer.py --reindex")

if __name__ == "__main__":
    main()
