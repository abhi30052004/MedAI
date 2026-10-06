"""
OCR and PDF text extraction pipeline.
- PDF: extract text per page with PyMuPDF (fitz)
- If a page has little/no text, render at high DPI and OCR with Tesseract
- Images: OCR directly
- OCRProvider interface so cloud OCR can be swapped in later
"""
import abc
import io
import os
import shutil
from typing import List, Optional, Tuple

from app.core.config import settings


def _resolve_tesseract_command() -> str:
    """Resolve an explicit setting, PATH entry, or common Windows install."""
    configured = settings.TESSERACT_CMD
    if os.path.isabs(configured) and os.path.isfile(configured):
        return configured
    path_match = shutil.which(configured)
    if path_match:
        return path_match
    if os.name == "nt":
        candidates = [
            os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
            os.path.join(os.getenv("ProgramFiles", ""), "Tesseract-OCR", "tesseract.exe"),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
    return configured


class OCRProvider(abc.ABC):
    """Abstract OCR provider."""

    @abc.abstractmethod
    def ocr_image(self, image_bytes: bytes) -> str:
        """OCR an image and return extracted text."""
        ...


class TesseractProvider(OCRProvider):
    """OCR using pytesseract + Pillow."""

    def ocr_image(self, image_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image

            pytesseract.pytesseract.tesseract_cmd = _resolve_tesseract_command()
            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            raise RuntimeError("OCR failed while processing the image") from e


class UnavailableOCRProvider(OCRProvider):
    """Fail explicitly when the required OCR runtime is unavailable."""

    def ocr_image(self, image_bytes: bytes) -> str:
        raise RuntimeError("OCR is unavailable because the Tesseract runtime is not installed")


def _get_ocr_provider() -> OCRProvider:
    """Return the best available OCR provider."""
    try:
        import pytesseract
        # Quick check that tesseract binary exists
        pytesseract.pytesseract.tesseract_cmd = _resolve_tesseract_command()
        pytesseract.get_tesseract_version()
        return TesseractProvider()
    except Exception:
        return UnavailableOCRProvider()


ocr_provider: OCRProvider = _get_ocr_provider()


# ── Text-extraction threshold ───────────────────────────────────
# If a PDF page yields fewer characters than this, consider it scanned
_MIN_TEXT_CHARS = 50


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[List[str], str]:
    """
    Extract text from a PDF.
    Returns (page_texts: list[str], full_text: str).
    For pages with little text, falls back to OCR.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts: List[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        if len(text) < _MIN_TEXT_CHARS:
            # Page is likely scanned — render to image and OCR
            dpi = settings.OCR_DPI
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            text = ocr_provider.ocr_image(img_bytes)

        page_texts.append(text)

    doc.close()
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(page_texts)
    return page_texts, full_text


def extract_text_from_image(image_bytes: bytes) -> Tuple[List[str], str]:
    """
    OCR a single image file.
    Returns (page_texts: [text], full_text: str).
    """
    text = ocr_provider.ocr_image(image_bytes)
    return [text], text


def extract_text_from_docx(docx_bytes: bytes) -> Tuple[List[str], str]:
    """Extract paragraphs and table cells from a DOCX document."""
    from docx import Document as DocxDocument

    document = DocxDocument(io.BytesIO(docx_bytes))
    blocks = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                blocks.append(" | ".join(cells))
    text = "\n".join(blocks)
    return [text], text


def extract_text(file_bytes: bytes, mime_type: str) -> Tuple[List[str], str]:
    """
    Unified extraction entry point.
    Dispatches based on MIME type.
    """
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif mime_type.startswith("image/"):
        return extract_text_from_image(file_bytes)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_bytes)
    else:
        # For other types (DOCX etc.), return empty — extend later
        return [], ""
