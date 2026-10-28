from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path


_OCR_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="receipt-ocr",
)


def _extract_receipt_text_worker(content, filename):
    extension = Path(filename).suffix.casefold()

    if extension == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError(
                "PDF receipt reading is unavailable. Install the pypdf "
                "package to enable it."
            ) from error

        try:
            reader = PdfReader(BytesIO(content))
            extracted_text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as error:
            raise RuntimeError(f"Unable to read PDF text: {error}") from error

        if extracted_text.strip():
            return extracted_text

        try:
            import fitz
            from PIL import Image
            import pytesseract
        except ImportError as error:
            raise RuntimeError(
                "This PDF appears to be scanned. Install PyMuPDF, Pillow, "
                "and pytesseract, and make sure Tesseract OCR is installed."
            ) from error

        try:
            document = fitz.open(stream=content, filetype="pdf")
            page_text = []
            for page in document[:10]:
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False,
                )
                image = Image.frombytes(
                    "RGB",
                    (pixmap.width, pixmap.height),
                    pixmap.samples,
                )
                page_text.append(pytesseract.image_to_string(image))
            return "\n".join(page_text)
        except pytesseract.TesseractNotFoundError as error:
            raise RuntimeError(
                "Tesseract OCR is not installed or is not on the system PATH."
            ) from error
        except Exception as error:
            raise RuntimeError(
                f"Unable to OCR this scanned PDF: {error}"
            ) from error

    try:
        from PIL import Image
        import pytesseract
    except ImportError as error:
        raise RuntimeError(
            "Image receipt OCR is unavailable. Install Pillow and "
            "pytesseract, and make sure the Tesseract OCR engine is installed."
        ) from error

    try:
        return pytesseract.image_to_string(Image.open(BytesIO(content)))
    except pytesseract.TesseractNotFoundError as error:
        raise RuntimeError(
            "Tesseract OCR is not installed or is not on the system PATH."
        ) from error
    except Exception as error:
        raise RuntimeError(f"Unable to OCR this image: {error}") from error


def extract_receipt_text(content, filename):
    """Run receipt text extraction on a worker thread and return its result."""

    future = _OCR_EXECUTOR.submit(
        _extract_receipt_text_worker,
        content,
        filename,
    )
    return future.result()
