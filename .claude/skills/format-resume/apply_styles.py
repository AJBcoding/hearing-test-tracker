#!/usr/bin/env python3
"""
Format CV content using template styles.

Usage:
    python format_cv.py input.json output.docx [--preview]

Input format: JSON with content mapping
"""
import sys
import json
from pathlib import Path
from cv_formatting.style_applicator import StyleApplicator
from cv_formatting.pdf_converter import PDFConverter
from cv_formatting.image_generator import ImageGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Format CV from content mapping."""
    if len(sys.argv) < 3:
        print("Usage: python format_cv.py <input.json> <output.docx> [--preview]")
        print("\nInput JSON format:")
        print('[')
        print('  {"text": "EDUCATION", "style": "Section Header", "type": "paragraph"},')
        print('  {"text": "Body text", "style": "Body Text", "type": "paragraph"}')
        print(']')
        print("\nOptions:")
        print("  --preview  Generate PDF and page images for visual verification")
        return 1

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    preview = '--preview' in sys.argv

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1

    # Load content mapping
    try:
        with open(input_file) as f:
            content_mapping = json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse input JSON: {e}")
        return 1

    # Get template
    template_path = Path.home() / ".claude/skills/career/format-resume/cv-template.docx"

    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        logger.error("Run generate_cv_template.py first")
        return 1

    # Apply styles
    logger.info(f"Formatting {len(content_mapping)} content items...")
    applicator = StyleApplicator(str(template_path))

    if not applicator.apply_styles(content_mapping, str(output_file)):
        logger.error("Formatting failed")
        return 1

    logger.info(f"✓ Formatted document: {output_file}")

    # Generate preview if requested
    if preview:
        logger.info("\nGenerating preview...")

        # Convert to PDF
        pdf_converter = PDFConverter()
        pdf_path = output_file.with_suffix('.pdf')

        if pdf_converter.is_available():
            logger.info("PDF conversion: available")
            if pdf_converter.convert_to_pdf(str(output_file), str(pdf_path)):
                logger.info(f"✓ PDF: {pdf_path}")

                # Convert to images
                image_gen = ImageGenerator()
                image_dir = output_file.parent / f"{output_file.stem}_images"

                if image_gen.is_available():
                    logger.info("Image generation: available")
                    images = image_gen.generate_images(str(pdf_path), str(image_dir))

                    if images:
                        logger.info(f"✓ Preview images: {image_dir}/")
                        logger.info(f"  Generated {len(images)} page images")
                        for img in images:
                            logger.info(f"  - {img.name}")
                    else:
                        logger.warning("Image generation failed")
                else:
                    logger.info("Image generation: skipped (pdftoppm not available)")
            else:
                logger.warning("PDF conversion failed")
        else:
            logger.info("PDF conversion: skipped (LibreOffice not available)")
            logger.info("Image generation: skipped (requires PDF)")

    return 0


if __name__ == '__main__':
    sys.exit(main())
