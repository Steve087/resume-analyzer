import os
import fitz
import docx
import langdetect
from langdetect import detect

class EmptyTextExtractionError(Exception):
    pass

class ScannedPDFError(Exception):
    pass

class UnsupportedLanguageError(Exception):
    pass

class CorruptFileError(Exception):
    pass

def extract_document_text(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file size — empty file
    if os.path.getsize(file_path) == 0:
        raise EmptyTextExtractionError(f"File is empty: {file_path}")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    try:
        if ext == '.pdf':
            extracted_text = _extract_pdf(file_path)
        elif ext == '.docx':
            extracted_text = _extract_docx(file_path)
        elif ext == '.doc':
            raise ValueError("'.doc' format not supported. Please convert to .docx first.")
        else:
            raise ValueError(f"Unsupported file type: '{ext}'. Only PDF and DOCX supported.")
    except (fitz.FileDataError, Exception) as e:
        if "cannot open" in str(e).lower() or "invalid" in str(e).lower():
            raise CorruptFileError(f"File appears to be corrupt: {file_path}")
        raise

    cleaned_text = extracted_text.strip()

    if not cleaned_text:
        raise EmptyTextExtractionError(
            f"No readable text extracted from '{file_path}'. "
            "This may be a scanned image PDF with no OCR layer."
        )

    # Language detection
    try:
        lang = detect(cleaned_text)
        if lang != 'en':
            raise UnsupportedLanguageError(
                f"Resume appears to be in a non-English language (detected: {lang}). "
                "The system currently supports English resumes only."
            )
    except UnsupportedLanguageError:
        raise
    except Exception:
        pass  # If language detection fails, continue anyway

    return cleaned_text[:6000]


def _extract_pdf(filepath: str) -> str:
    try:
        with fitz.open(filepath) as doc:
            if doc.is_encrypted:
                raise CorruptFileError(f"PDF is password-protected: {filepath}")
            pages_text = []
            for page in doc:
                text = page.get_text("text")
                if text:
                    pages_text.append(text)
            return "\n".join(pages_text)
    except fitz.FileDataError:
        raise CorruptFileError(f"PDF file is corrupt or unreadable: {filepath}")


def _extract_docx(filepath: str) -> str:
    try:
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception:
        raise CorruptFileError(f"DOCX file is corrupt or unreadable: {filepath}")