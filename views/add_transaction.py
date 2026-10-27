import hashlib
import re
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import streamlit as st

from database import MAX_AMOUNT, MAX_DESCRIPTION_LENGTH, add_transaction
from utils.formatting import money, suggest_category


FLASH_KEY = "add_transaction_flash"
RECEIPT_STATE_KEY = "receipt_processed_hash"
RECEIPT_ERROR_KEY = "receipt_error"
AMOUNT_KEY = "transaction_amount"
DATE_KEY = "transaction_date"
DESCRIPTION_KEY = "transaction_description"


def _apply_category_suggestion(description, transaction_type, categories):
    category_key = f"category_{transaction_type}"
    description_key = f"category_suggestion_description_{transaction_type}"

    if st.session_state.get(description_key) == description:
        return

    st.session_state[description_key] = description
    suggestion = suggest_category(description)
    if suggestion in categories:
        st.session_state[category_key] = suggestion


def _extract_receipt_text(uploaded_file):
    content = uploaded_file.getvalue()
    extension = Path(uploaded_file.name).suffix.casefold()

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
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
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


def _parse_receipt_amount(text):
    amount_pattern = re.compile(
        r"(?<![\w/])(?:₹|Rs\.?|INR)\s*"
        r"(\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)",
        re.IGNORECASE,
    )
    labelled_pattern = re.compile(
        r"(?:grand\s+total|total\s+amount|amount\s+paid|total|paid)"
        r"\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*"
        r"(\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)",
        re.IGNORECASE,
    )

    for line in text.splitlines():
        match = labelled_pattern.search(line)
        if match:
            amount = float(match.group(1).replace(",", ""))
            if 0 < amount <= MAX_AMOUNT:
                return amount

    for match in amount_pattern.finditer(text):
        amount = float(match.group(1).replace(",", ""))
        if 0 < amount <= MAX_AMOUNT:
            return amount

    bare_amount_pattern = re.compile(
        r"(?<![\w/])(\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\w/])"
    )
    excluded_line = re.compile(
        r"\b(invoice|receipt|gstin|phone|mobile|order|reference|"
        r"account|pin|zip|date|time)\b",
        re.IGNORECASE,
    )
    for line in reversed(text.splitlines()):
        if re.search(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", line):
            continue
        if excluded_line.search(line):
            continue
        for match in bare_amount_pattern.finditer(line):
            amount = float(match.group(1).replace(",", ""))
            if 0 < amount <= MAX_AMOUNT and (
                "." in match.group(1) or amount >= 100
            ):
                return amount

    return None


def _parse_receipt_date(text, today):
    patterns = (
        (r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", ("%Y-%m-%d", "%Y/%m/%d")),
        (
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",
            ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"),
        ),
        (
            r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
            ("%d %B %Y", "%d %b %Y"),
        ),
    )

    for pattern, formats in patterns:
        for match in re.finditer(pattern, text):
            for date_format in formats:
                try:
                    parsed_date = datetime.strptime(
                        match.group(),
                        date_format,
                    ).date()
                except ValueError:
                    continue
                if date(2000, 1, 1) <= parsed_date <= today:
                    return parsed_date

    return None


def _parse_receipt_description(text, filename):
    ignored_words = (
        "receipt",
        "invoice",
        "tax invoice",
        "date",
        "total",
        "amount",
        "gst",
        "cashier",
        "thank you",
    )
    for line in text.splitlines():
        candidate = " ".join(line.split()).strip(" -:|")
        if (
            2 <= len(candidate) <= MAX_DESCRIPTION_LENGTH
            and not any(word in candidate.casefold() for word in ignored_words)
            and not re.search(r"\d{2,}", candidate)
        ):
            return candidate

    return Path(filename).stem[:MAX_DESCRIPTION_LENGTH]


def render_add_transaction(expense_categories, income_categories, today):
    """Render the Add Transaction page."""

    st.markdown(
        '<div class="ss-eyebrow">SPENDSENSE AI · NEW ENTRY</div>'
        '<div class="ss-page-title">Add a transaction.</div>'
        '<div class="ss-subtitle">'
        "Record your income and daily expenses in a few seconds."
        "</div>",
        unsafe_allow_html=True,
    )

    # Message saved before the rerun, so it is visible after saving.
    flash = st.session_state.pop(FLASH_KEY, None)

    if flash:
        st.toast("✅ Transaction saved successfully!", icon="💸")

    st.session_state.setdefault(DATE_KEY, today)
    st.session_state.setdefault(DESCRIPTION_KEY, "")

    receipt = st.file_uploader(
        "Upload bill / receipt (OCR)",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Upload a JPG, PNG, or PDF. Extracted details are suggestions; "
        "please check them before saving.",
        key="transaction_receipt_uploader",
    )

    if receipt is not None:
        receipt_hash = hashlib.sha256(receipt.getvalue()).hexdigest()
        receipt_error = st.session_state.get(RECEIPT_ERROR_KEY)
        if receipt_error and receipt_error[0] == receipt_hash:
            st.error(f"Could not read this receipt: {receipt_error[1]}")

        if st.session_state.get(RECEIPT_STATE_KEY) != receipt_hash:
            st.session_state.pop(RECEIPT_ERROR_KEY, None)
            try:
                receipt_text = _extract_receipt_text(receipt)
            except (RuntimeError, OSError, ValueError) as error:
                st.session_state[RECEIPT_STATE_KEY] = receipt_hash
                st.session_state[RECEIPT_ERROR_KEY] = (
                    receipt_hash,
                    str(error),
                )
            else:
                detected = []
                amount_value = _parse_receipt_amount(receipt_text)
                date_value = _parse_receipt_date(receipt_text, today)
                description_value = _parse_receipt_description(
                    receipt_text,
                    receipt.name,
                )

                if amount_value is not None:
                    st.session_state[AMOUNT_KEY] = amount_value
                    detected.append("amount")
                if date_value is not None:
                    st.session_state[DATE_KEY] = date_value
                    detected.append("date")
                if description_value:
                    st.session_state[DESCRIPTION_KEY] = description_value
                    detected.append("description")

                if detected:
                    st.success(
                        "Receipt details detected for "
                        f"{', '.join(detected)}. Please verify before saving."
                    )
                else:
                    st.warning(
                        "No transaction details could be confidently "
                        "detected. You can enter them manually."
                    )
                st.session_state[RECEIPT_STATE_KEY] = receipt_hash

    else:
        st.session_state.pop(RECEIPT_STATE_KEY, None)
        st.session_state.pop(RECEIPT_ERROR_KEY, None)

    with st.container(border=True):

        # Type and category stay outside the form so the category
        # list updates immediately when the type changes.
        transaction_type = st.radio(
            "Transaction Type",
            ["Expense", "Income"],
            horizontal=True,
            key="transaction_type_selector",
        )

        placeholder = (
            "Example: Groceries"
            if transaction_type == "Expense"
            else "Example: Monthly salary"
        )
        description = st.text_input(
            "Description (optional)",
            placeholder=placeholder,
            max_chars=MAX_DESCRIPTION_LENGTH,
            key=DESCRIPTION_KEY,
        )

        categories = (
            expense_categories
            if transaction_type == "Expense"
            else income_categories
        )
        _apply_category_suggestion(description, transaction_type, categories)

        category = st.selectbox(
            "Category",
            categories,
            key=f"category_{transaction_type}",
        )

        with st.form("transaction_form", clear_on_submit=False):

            amount_col, date_col = st.columns(2, gap="medium")

            with amount_col:
                amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.01,
                    max_value=float(MAX_AMOUNT),
                    value=None,
                    step=100.0,
                    format="%.2f",
                    placeholder="Enter amount",
                    key=AMOUNT_KEY,
                )

            with date_col:
                transaction_date = st.date_input(
                    "Transaction Date",
                    min_value=date(2000, 1, 1),
                    max_value=today,
                    key=DATE_KEY,
                )

            submitted = st.form_submit_button(
                f"Save {transaction_type}",
                use_container_width=True,
            )

    if not submitted:
        return

    if amount is None:
        st.error("Please enter an amount before saving.")
        return

    try:
        add_transaction(
            transaction_type=transaction_type,
            amount=float(amount),
            category=category,
            description=description.strip(),
            transaction_date=transaction_date.isoformat(),
        )

    except (ValueError, TypeError) as error:
        st.error(str(error))
        return

    except Exception:
        st.error(
            "The transaction could not be saved. "
            "Please try again in a moment."
        )
        return

    # Rerun so the sidebar, dashboard, and reports use the new data.
    st.session_state[FLASH_KEY] = (
        f"{transaction_type} of {money(amount)} saved "
        f"under {category}."
    )
    st.rerun()