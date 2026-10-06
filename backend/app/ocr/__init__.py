"""
OCR and PDF text extraction pipeline.
- PDF: extract text per page with PyMuPDF (fitz)
- If a page has little/no text, render at high DPI and OCR with Tesseract
- Images: OCR directly
- OCRProvider interface so cloud OCR can be swapped in later
"""
import abc
import io
from typing import List, Optional, Tuple

from app.core.config import settings


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

            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            return f"[OCR Error: {e}]"


class MockOCRProvider(OCRProvider):
    """Fallback when Tesseract is not installed."""

    def ocr_image(self, image_bytes: bytes) -> str:
        return "[OCR not available — Tesseract not installed]"


def _get_ocr_provider() -> OCRProvider:
    """Return the best available OCR provider."""
    try:
        import pytesseract
        # Quick check that tesseract binary exists
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        pytesseract.get_tesseract_version()
        return TesseractProvider()
    except Exception:
        return MockOCRProvider()


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


def extract_text(file_bytes: bytes, mime_type: str) -> Tuple[List[str], str]:
    """
    Unified extraction entry point.
    Dispatches based on MIME type.
    """
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif mime_type.startswith("image/"):
        return extract_text_from_image(file_bytes)
    else:
        # For other types (DOCX etc.), return empty — extend later
        return [], ""
