from app.services.extraction_service import ExtractionService


def test_extract_docx_text(sample_docx_file):
    service = ExtractionService()
    result = service.extract(sample_docx_file, "docx")

    assert "Employee Policy" in result.text
    assert "12 casual leave days" in result.text
