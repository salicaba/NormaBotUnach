import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Text processing utilities
def clean_text(text: str) -> str:
    """Cleans extracted text by normalizing whitespace, linebreaks, and special chars."""
    if not text:
        return ""
    # Normalize multiple newlines and spaces
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class DocumentParser:
    """Parser for various document formats: PDF, DOCX, XLSX, TXT, Images."""

    def __init__(self, enable_ocr: bool = False):
        self.enable_ocr = enable_ocr
        self._ocr_instance = None

    def _get_ocr(self):
        """Lazy loader for RapidOCR."""
        if not self.enable_ocr:
            return None
        if self._ocr_instance is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._ocr_instance = RapidOCR()
            except Exception as e:
                print(f"[DocumentParser] OCR not available: {e}")
                self._ocr_instance = False
        return self._ocr_instance if self._ocr_instance is not False else None

    def parse_file(self, file_path: str | Path) -> Optional[Dict[str, Any]]:
        """Parses a document based on its file extension."""
        path = Path(file_path)
        if not path.exists():
            return None

        ext = path.suffix.lower()
        filename = path.name

        try:
            if ext == ".pdf":
                return self._parse_pdf(path)
            elif ext in [".docx", ".doc"]:
                return self._parse_docx(path)
            elif ext in [".xlsx", ".xls"]:
                return self._parse_xlsx(path)
            elif ext in [".txt", ".csv", ".md"]:
                return self._parse_text(path)
            elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
                return self._parse_image(path)
            else:
                print(f"[DocumentParser] Unsupported format: {ext} for {filename}")
                return None
        except Exception as e:
            print(f"[DocumentParser] Error parsing {filename}: {e}")
            return None

    def _parse_pdf(self, path: Path) -> Dict[str, Any]:
        """Extracts text and page numbers from a PDF file."""
        import pypdf

        pages_data = []
        reader = pypdf.PdfReader(str(path))
        num_pages = len(reader.pages)

        # For performance, only run OCR on short scanned agreements (<= 15 pages).
        # Large manuals (80MB+) with hundreds of scanned pages are skipped from heavy OCR.
        should_attempt_ocr = self.enable_ocr and (num_pages <= 15)
        ocr = self._get_ocr() if should_attempt_ocr else None
        ocr_pages_count = 0
        max_ocr_pages = 8

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = ""
            try:
                text = page.extract_text() or ""
            except Exception as e:
                text = ""

            text = clean_text(text)

            # Check if page is empty or scanned (fewer than 30 characters)
            if len(text) < 30 and ocr and ocr_pages_count < max_ocr_pages:
                try:
                    if hasattr(page, "images") and len(page.images) > 0:
                        ocr_texts = []
                        for img in page.images:
                            ocr_res, _ = ocr(img.data)
                            if ocr_res:
                                ocr_texts.append(" ".join([line[1] for line in ocr_res]))
                        if ocr_texts:
                            text = clean_text(" ".join(ocr_texts))
                            ocr_pages_count += 1
                except Exception as e:
                    pass

            if text:
                pages_data.append({
                    "page_num": page_num,
                    "text": text
                })

        return {
            "filename": path.name,
            "filepath": str(path.resolve()),
            "format": "pdf",
            "total_pages": num_pages,
            "pages": pages_data,
            "has_text": len(pages_data) > 0
        }

    def _parse_docx(self, path: Path) -> Dict[str, Any]:
        """Extracts text from DOCX files with paragraph and table support."""
        import docx

        doc = docx.Document(str(path))
        paragraphs_text = []

        # Read regular paragraphs
        for p in doc.paragraphs:
            txt = clean_text(p.text)
            if txt:
                paragraphs_text.append(txt)

        # Read tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [clean_text(cell.text) for cell in row.cells if clean_text(cell.text)]
                if row_cells:
                    paragraphs_text.append(" | ".join(row_cells))

        full_text = "\n\n".join(paragraphs_text)

        # Split into pseudo-pages (~1200 characters per page for consistent chunking)
        chunk_size = 1200
        pages_data = []
        lines = full_text.split("\n\n")
        current_page_text = []
        current_len = 0
        page_num = 1

        for line in lines:
            current_page_text.append(line)
            current_len += len(line)
            if current_len >= chunk_size:
                pages_data.append({
                    "page_num": page_num,
                    "text": "\n\n".join(current_page_text)
                })
                page_num += 1
                current_page_text = []
                current_len = 0

        if current_page_text:
            pages_data.append({
                "page_num": page_num,
                "text": "\n\n".join(current_page_text)
            })

        return {
            "filename": path.name,
            "filepath": str(path.resolve()),
            "format": "docx",
            "total_pages": len(pages_data),
            "pages": pages_data,
            "has_text": len(pages_data) > 0
        }

    def _parse_xlsx(self, path: Path) -> Dict[str, Any]:
        """Extracts structured text summaries from Excel spreadsheets."""
        import openpyxl

        wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
        pages_data = []

        for idx, sheet_name in enumerate(wb.sheetnames):
            sheet = wb[sheet_name]
            sheet_rows = []
            row_count = 0

            for row in sheet.iter_rows(values_only=True):
                non_empty = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                if non_empty:
                    sheet_rows.append(" | ".join(non_empty))
                    row_count += 1
                    if row_count > 200:  # Cap very long rows per sheet for speed
                        sheet_rows.append("... [Más filas en la hoja]")
                        break

            if sheet_rows:
                sheet_text = f"Hoja: {sheet_name}\n" + "\n".join(sheet_rows)
                pages_data.append({
                    "page_num": idx + 1,
                    "sheet_name": sheet_name,
                    "text": clean_text(sheet_text)
                })

        return {
            "filename": path.name,
            "filepath": str(path.resolve()),
            "format": "xlsx",
            "total_pages": len(pages_data),
            "pages": pages_data,
            "has_text": len(pages_data) > 0
        }

    def _parse_text(self, path: Path) -> Dict[str, Any]:
        """Reads plain text / markdown / CSV files."""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        clean = clean_text(content)
        pages_data = [{"page_num": 1, "text": clean}] if clean else []

        return {
            "filename": path.name,
            "filepath": str(path.resolve()),
            "format": "text",
            "total_pages": 1,
            "pages": pages_data,
            "has_text": len(pages_data) > 0
        }

    def _parse_image(self, path: Path) -> Dict[str, Any]:
        """Extracts text from images using OCR."""
        ocr = self._get_ocr()
        pages_data = []

        if ocr:
            try:
                from PIL import Image
                img = Image.open(path)
                ocr_res, _ = ocr(str(path))
                if ocr_res:
                    text = clean_text(" ".join([line[1] for line in ocr_res]))
                    if text:
                        pages_data.append({"page_num": 1, "text": text})
            except Exception as e:
                print(f"[DocumentParser] Error in image OCR for {path.name}: {e}")

        return {
            "filename": path.name,
            "filepath": str(path.resolve()),
            "format": "image",
            "total_pages": 1,
            "pages": pages_data,
            "has_text": len(pages_data) > 0
        }
