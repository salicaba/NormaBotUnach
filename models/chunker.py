import re
from typing import List, Dict, Any

class SmartChunker:
    """
    Intelligent chunker for legal, normative, and academic documents of UNACH.
    Preserves article boundaries, chapter context, and page numbers.
    """

    ARTICLE_REGEX = re.compile(
        r'(?:^|\n)\s*(ART[ÍI]CULO\s+\d+[\s\.:\-\w]*|ART\.\s*\d+[\s\.:\-\w]*)',
        re.IGNORECASE
    )
    SECTION_REGEX = re.compile(
        r'(?:^|\n)\s*(T[ÍI]TULO\s+[IVXLCDM\d]+[^\n]*|CAP[ÍI]TULO\s+[IVXLCDM\d]+[^\n]*|SECCI[ÓO]N\s+[IVXLCDM\d]+[^\n]*)',
        re.IGNORECASE
    )

    def __init__(self, target_chunk_size: int = 800, overlap: int = 150):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def chunk_document(self, parsed_doc: Dict[str, Any], category: str = "general") -> List[Dict[str, Any]]:
        """Splits parsed document pages into coherent chunks."""
        chunks = []
        filename = parsed_doc.get("filename", "")
        pages = parsed_doc.get("pages", [])

        current_header = ""

        for page_info in pages:
            page_num = page_info.get("page_num", 1)
            sheet_name = page_info.get("sheet_name", "")
            text = page_info.get("text", "")

            if not text:
                continue

            # Detect section/chapter headers in the page
            headers = self.SECTION_REGEX.findall(text)
            if headers:
                current_header = headers[-1].strip()

            # Attempt article-based splitting for normative documents
            splits = self.ARTICLE_REGEX.split(text)

            if len(splits) > 1:
                # We found articles!
                # splits[0] is pre-article text, then alternating [match, content, match, content]
                pre_text = splits[0].strip()
                if len(pre_text) > 80:
                    chunks.append(self._create_chunk(
                        filename=filename,
                        page_num=page_num,
                        sheet_name=sheet_name,
                        header=current_header,
                        article_ref="Disposiciones Generales",
                        content=pre_text,
                        category=category
                    ))

                for i in range(1, len(splits), 2):
                    art_ref = splits[i].strip()
                    art_content = splits[i+1].strip() if i+1 < len(splits) else ""
                    full_art_text = f"{art_ref} - {art_content}"

                    # If article is very long, split into subchunks
                    if len(full_art_text) > self.target_chunk_size * 2:
                        subchunks = self._sliding_window(full_art_text, self.target_chunk_size, self.overlap)
                        for sub_idx, sub in enumerate(subchunks):
                            chunks.append(self._create_chunk(
                                filename=filename,
                                page_num=page_num,
                                sheet_name=sheet_name,
                                header=current_header,
                                article_ref=f"{art_ref} (Parte {sub_idx+1})",
                                content=sub,
                                category=category
                            ))
                    else:
                        chunks.append(self._create_chunk(
                            filename=filename,
                            page_num=page_num,
                            sheet_name=sheet_name,
                            header=current_header,
                            article_ref=art_ref,
                            content=full_art_text,
                            category=category
                        ))
            else:
                # If no article markers, use sliding window paragraph chunker
                paras = text.split("\n\n")
                buf = []
                buf_len = 0

                for p in paras:
                    p = p.strip()
                    if not p:
                        continue
                    buf.append(p)
                    buf_len += len(p)

                    if buf_len >= self.target_chunk_size:
                        chunk_text = "\n\n".join(buf)
                        chunks.append(self._create_chunk(
                            filename=filename,
                            page_num=page_num,
                            sheet_name=sheet_name,
                            header=current_header,
                            article_ref=f"Página {page_num}",
                            content=chunk_text,
                            category=category
                        ))
                        # Keep last paragraph for overlap
                        buf = [buf[-1]] if len(buf) > 1 else []
                        buf_len = len(buf[0]) if buf else 0

                if buf:
                    chunk_text = "\n\n".join(buf)
                    if len(chunk_text) > 40:
                        chunks.append(self._create_chunk(
                            filename=filename,
                            page_num=page_num,
                            sheet_name=sheet_name,
                            header=current_header,
                            article_ref=f"Página {page_num}",
                            content=chunk_text,
                            category=category
                        ))

        return chunks

    def _sliding_window(self, text: str, size: int, overlap: int) -> List[str]:
        """Splits long text with overlapping windows."""
        results = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + size, text_len)
            # Try to snap end to a space or sentence end
            if end < text_len:
                last_space = text.rfind(" ", start, end)
                if last_space > start + size // 2:
                    end = last_space
            results.append(text[start:end].strip())
            start = end - overlap if end < text_len else text_len
            if start >= end:
                break
        return results

    def _create_chunk(self, filename: str, page_num: int, sheet_name: str,
                      header: str, article_ref: str, content: str, category: str) -> Dict[str, Any]:
        """Formats single chunk dictionary."""
        # Clean up readable document name
        doc_title = filename.replace("-", " ").replace("_", " ")
        if doc_title.lower().endswith(".pdf"):
            doc_title = doc_title[:-4]
        elif doc_title.lower().endswith(".docx") or doc_title.lower().endswith(".xlsx"):
            doc_title = doc_title[:-5]

        return {
            "document": filename,
            "document_title": doc_title.strip(),
            "category": category,
            "page": page_num,
            "sheet": sheet_name,
            "header": header,
            "article_ref": article_ref,
            "content": content,
            "char_count": len(content)
        }
