import os
import fitz  # PyMuPDF
import docx

class EmptyTextExtractionError(Exception):
    """Custom exception raised when no text can be extracted from a file."""
    pass

def extract_document_text(file_path: str) -> str:
    """
    Extracts text from .pdf or .docx files.
    Raises EmptyTextExtractionError if the resulting text is empty.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    extracted_text = ""

    if ext == '.pdf':
        # Open the PDF with PyMuPDF
        with fitz.open(file_path) as pdf:
            pages_text = []
            for page in pdf:
                # Extract text preserving reading order blocks where possible
                text = page.get_text("text") 
                if text:
                    pages_text.append(text)
            extracted_text = "\n".join(pages_text)
            
    elif ext == '.docx':
        doc = docx.Document(file_path)
        extracted_text = "\n".join([para.text for para in doc.paragraphs])
        
    else:
        raise ValueError(f"Unsupported file extension: '{ext}'. Only .pdf and .docx are supported.")

    cleaned_text = extracted_text.strip()

    if not cleaned_text:
        raise EmptyTextExtractionError(
            f"No readable text could be extracted from '{file_path}'. "
            "This may be an empty document or a scanned image lacking an OCR layer."
        )

    return cleaned_text
