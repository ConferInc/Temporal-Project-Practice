"""
Test suite for the Document Splitter pre-processing layer.

Tests the function-based API in src/preprocessing/splitter.py:
  - split_document_blob()
  - is_mega_pdf()
  - cleanup_chunks()
  - _match_page() (signature matching)
  - _keyword_in_text() (OCR word-fusion resilience)

Creates test PDFs programmatically with fitz (PyMuPDF).
"""

import os
import sys
import pytest
import fitz  # PyMuPDF

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.preprocessing.splitter import (
    split_document_blob,
    is_mega_pdf,
    cleanup_chunks,
    _match_page,
    _keyword_in_text,
)


# ==================================================================
# Helpers
# ==================================================================

def create_test_pdf(pages: list, output_path: str):
    """Create a PDF where each page contains the given text."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(output_path)
    doc.close()


# Canonical text snippets that trigger signatures
W2_TEXT = (
    "Form W-2  Wage and Tax Statement  2023\n"
    "Department of the Treasury\n"
    "Employer identification number (EIN) 12-3456789\n"
    "Employee's social security number 999-60-5555\n"
    "Federal income tax withheld  9867.72\n"
)

BANK_TEXT = (
    "Bank of America  Account Summary\n"
    "Statement Period: 01/01/2025 - 01/31/2025\n"
    "Beginning Balance  $25,000.00\n"
    "Ending Balance  $27,500.00\n"
    "Checking Account  ****1234\n"
)

URLA_TEXT = (
    "Uniform Residential Loan Application\n"
    "Form 1003\n"
    "Borrower Information\n"
    "Agency Case Number  999-1234567-001\n"
    "Lender Case Number  55443\n"
    "Type of Mortgage  Conventional\n"
    "Subject Property Address  123 Main Street\n"
)

PAYSTUB_TEXT = (
    "Earnings Statement\n"
    "Pay Period  01/01/2025 - 01/15/2025\n"
    "Pay Begin Date  01/01/2025\n"
    "Pay End Date  01/15/2025\n"
    "Net Pay  $2,269.23\n"
    "Total Gross  $3,692.31\n"
    "YTD  $3,692.31\n"
)

GENERIC_TEXT = (
    "This is a generic page with no specific mortgage document signatures.\n"
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
)


# ==================================================================
# Tests: OCR word-fusion resilience
# ==================================================================

class TestKeywordInText:
    """Test _keyword_in_text handles OCR-fused words."""

    def test_normal_spaced_text(self):
        assert _keyword_in_text("wage and tax statement", "form w-2 wage and tax statement")

    def test_fused_words(self):
        """OCR often fuses words: 'UniformResidentialLoanApplication'."""
        assert _keyword_in_text(
            "uniform residential loan application",
            "somefinancialgroup,llc uniformresidentialloanapplication"
        )

    def test_single_word(self):
        assert _keyword_in_text("w-2", "form w-2 stuff")

    def test_no_match(self):
        assert not _keyword_in_text("uniform residential loan application", "hello world")

    def test_partial_match(self):
        """Only 2 of 4 words present -> should fail."""
        assert not _keyword_in_text("uniform residential loan application", "uniform loan")


# ==================================================================
# Tests: Signature matching  (_match_page returns tuple)
# ==================================================================

class TestSignatureMatching:
    def test_w2_match(self):
        doc_type, score = _match_page(W2_TEXT)
        assert doc_type == "W-2 Form"
        assert score > 0

    def test_bank_match(self):
        doc_type, score = _match_page(BANK_TEXT)
        assert doc_type == "Bank Statement"
        assert score > 0

    def test_urla_match(self):
        doc_type, score = _match_page(URLA_TEXT)
        assert doc_type == "URLA (Form 1003)"
        assert score > 0

    def test_paystub_match(self):
        doc_type, score = _match_page(PAYSTUB_TEXT)
        assert doc_type == "Pay Stub"
        assert score > 0

    def test_no_match(self):
        doc_type, score = _match_page(GENERIC_TEXT)
        assert doc_type is None
        assert score == 0.0

    def test_empty_text(self):
        assert _match_page("") == (None, 0.0)
        assert _match_page("   ") == (None, 0.0)

    def test_urla_fused_ocr(self):
        """Simulate OCR-fused URLA text."""
        fused = "UniformResidentialLoanApplication BorrowerInformation Form1003"
        doc_type, score = _match_page(fused)
        assert doc_type == "URLA (Form 1003)"

    def test_w2_fused_ocr(self):
        """Simulate OCR-fused W-2 text."""
        fused = "WageandTaxStatement employeridentificationnumber federalincometaxwithheld"
        doc_type, score = _match_page(fused)
        assert doc_type == "W-2 Form"


# ==================================================================
# Tests: split_document_blob()
# ==================================================================

class TestSinglePageW2:
    """1-page W-2 text -> 1 chunk"""

    def test_single_page_w2(self, tmp_path):
        pdf_path = str(tmp_path / "single_w2.pdf")
        create_test_pdf([W2_TEXT], pdf_path)

        paths = split_document_blob(pdf_path)
        assert len(paths) == 1
        assert os.path.isfile(paths[0])
        assert "W-2Form" in paths[0]

        cleanup_chunks(paths)


class TestTwoDifferentDocs:
    """W-2 page + BankStatement page -> 2 chunks"""

    def test_two_different_docs(self, tmp_path):
        pdf_path = str(tmp_path / "two_docs.pdf")
        create_test_pdf([W2_TEXT, BANK_TEXT], pdf_path)

        paths = split_document_blob(pdf_path)
        assert len(paths) == 2

        cleanup_chunks(paths)


class TestContinuationPages:
    """URLA page + 4 unmatched pages -> 1 chunk (5 pages)"""

    def test_continuation_pages(self, tmp_path):
        pdf_path = str(tmp_path / "urla_multi.pdf")
        pages = [URLA_TEXT] + [GENERIC_TEXT] * 4
        create_test_pdf(pages, pdf_path)

        paths = split_document_blob(pdf_path)
        assert len(paths) == 1
        assert "URLAForm1003" in paths[0]

        cleanup_chunks(paths)


class TestBackPage:
    """W-2 page + blank page -> 1 chunk"""

    def test_back_page(self, tmp_path):
        pdf_path = str(tmp_path / "w2_back.pdf")
        create_test_pdf([W2_TEXT, ""], pdf_path)

        paths = split_document_blob(pdf_path)
        assert len(paths) == 1

        cleanup_chunks(paths)


class TestUnknownFirstPage:
    """Unmatched page + W-2 page -> 2 chunks (Unknown + W-2)"""

    def test_unknown_first(self, tmp_path):
        pdf_path = str(tmp_path / "unknown_first.pdf")
        create_test_pdf([GENERIC_TEXT, W2_TEXT], pdf_path)

        paths = split_document_blob(pdf_path)
        assert len(paths) == 2
        assert "Unknown" in paths[0]
        assert "W-2Form" in paths[1]

        cleanup_chunks(paths)


class TestSameTypeTwice:
    """W-2 + PayStub + W-2 -> 3 chunks"""

    def test_same_type_twice(self, tmp_path):
        pdf_path = str(tmp_path / "w2_ps_w2.pdf")
        create_test_pdf([W2_TEXT, PAYSTUB_TEXT, W2_TEXT], pdf_path)

        paths = split_document_blob(pdf_path)
        assert len(paths) == 3

        cleanup_chunks(paths)


# ==================================================================
# Tests: is_mega_pdf()
# ==================================================================

class TestIsMegaPdf:
    def test_is_mega_pdf_true(self, tmp_path):
        pdf_path = str(tmp_path / "mega.pdf")
        create_test_pdf([W2_TEXT, BANK_TEXT], pdf_path)
        assert is_mega_pdf(pdf_path) is True

    def test_is_mega_pdf_false(self, tmp_path):
        pdf_path = str(tmp_path / "single.pdf")
        create_test_pdf([W2_TEXT], pdf_path)
        assert is_mega_pdf(pdf_path) is False

    def test_is_mega_pdf_false_same_type(self, tmp_path):
        pdf_path = str(tmp_path / "same_type.pdf")
        create_test_pdf([W2_TEXT, W2_TEXT], pdf_path)
        assert is_mega_pdf(pdf_path) is False


# ==================================================================
# Tests: cleanup
# ==================================================================

class TestCleanup:
    def test_cleanup(self, tmp_path):
        pdf_path = str(tmp_path / "cleanup_test.pdf")
        create_test_pdf([W2_TEXT, BANK_TEXT], pdf_path)

        paths = split_document_blob(pdf_path)
        temp_dir = os.path.dirname(paths[0])

        assert os.path.isdir(temp_dir)
        for p in paths:
            assert os.path.isfile(p)

        cleanup_chunks(paths)
        assert not os.path.isdir(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
