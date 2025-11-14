"""Tests for OCR text extraction module."""
import pytest
from pathlib import Path
from backend.ocr.text_extractor import (
    parse_jacoti_footer,
    extract_jacoti_metadata
)


class TestParseJacotiFooter:
    """Test footer text parsing."""

    def test_parse_valid_footer(self):
        """Test parsing a standard Jacoti footer."""
        footer_text = "Made with Jacoti Hearing Center - 2024-12-17 12:24"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['date'] == '2024-12-17'
        assert result['time'] == '12:24'
        assert result['device'] == 'Jacoti Hearing Center'
        assert result['location'] == 'Jacoti Hearing Center'

    def test_parse_footer_with_variations(self):
        """Test parsing footer with OCR variations (e.g., dash types)."""
        # En-dash instead of hyphen
        footer_text = "Made with Jacoti Hearing Center – 2024-12-17 12:24"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['date'] == '2024-12-17'

    def test_parse_footer_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        footer_text = "made with Jacoti Hearing Center - 2024-12-17 12:24"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['device'] == 'Jacoti Hearing Center'

    def test_parse_footer_with_slash_date(self):
        """Test parsing footer with slash-separated date."""
        footer_text = "Made with Jacoti Hearing Center - 2024/12/17 12:24"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['date'] == '2024-12-17'  # Should be normalized to dash

    def test_parse_footer_fallback_date_only(self):
        """Test fallback to date-only extraction if full pattern fails."""
        footer_text = "Some other text 2024-12-17 more text"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['date'] == '2024-12-17'
        assert result['time'] is None
        assert result['device'] == 'Unknown'

    def test_parse_footer_no_match(self):
        """Test parsing with no valid date or pattern."""
        footer_text = "Invalid footer text with no date"
        result = parse_jacoti_footer(footer_text)

        assert result is None

    def test_parse_footer_with_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        footer_text = "Made with  Jacoti Hearing Center  -  2024-12-17  12:24"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['date'] == '2024-12-17'
        assert result['time'] == '12:24'

    def test_parse_footer_single_digit_hour(self):
        """Test parsing time with single-digit hour."""
        footer_text = "Made with Jacoti Hearing Center - 2024-12-17 9:30"
        result = parse_jacoti_footer(footer_text)

        assert result is not None
        assert result['time'] == '9:30'


class TestExtractJacotiMetadata:
    """Test full metadata extraction from audiogram images."""

    def test_extract_metadata_from_sample_image(self, tmp_path):
        """Test metadata extraction from a real Jacoti audiogram."""
        # Use the actual sample image from the archive
        sample_path = Path('/home/user/hearing-test-tracker/Hearing test Archive/Audiograms/2024-12-07.jpeg')

        if not sample_path.exists():
            pytest.skip("Sample audiogram not found")

        result = extract_jacoti_metadata(sample_path)

        # Check that we got a result
        assert result is not None
        assert 'date' in result
        assert 'time' in result
        assert 'device' in result
        assert 'location' in result
        assert 'raw_footer_text' in result

        # The actual values will depend on OCR accuracy, but we should get something
        print(f"Extracted metadata: {result}")

    def test_extract_metadata_invalid_path(self):
        """Test that invalid image path raises error."""
        invalid_path = Path('/nonexistent/image.jpg')

        with pytest.raises(ValueError, match="Cannot read image"):
            extract_jacoti_metadata(invalid_path)
