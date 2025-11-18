#!/usr/bin/env python3
"""Extract form field data from PDF files.

This script extracts fillable form fields (AcroForms) from PDF documents
and outputs them as JSON. Useful for processing completed forms programmatically.
"""

import argparse
import json
import sys
from pathlib import Path

from pypdf import PdfReader


def extract_form_fields(pdf_path: Path) -> dict:
    """Extract form fields from a PDF file.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        Dict with 'fields' (field_name: value) and 'metadata'.
    """
    try:
        reader = PdfReader(pdf_path)

        # Check if PDF has forms
        if reader.get_form_text_fields() is None and not hasattr(reader, "get_fields"):
            return {
                "fields": {},
                "metadata": {
                    "total_fields": 0,
                    "filled_fields": 0,
                    "message": "No form fields found in PDF",
                },
            }

        # Get form fields
        form_fields = reader.get_form_text_fields() or {}

        # Count filled fields
        filled = sum(1 for v in form_fields.values() if v)

        return {
            "fields": form_fields,
            "metadata": {
                "total_fields": len(form_fields),
                "filled_fields": filled,
            },
        }

    except Exception as e:
        return {
            "error": str(e),
            "fields": {},
            "metadata": {"total_fields": 0, "filled_fields": 0},
        }


def main():
    """Parse arguments and extract form data."""
    parser = argparse.ArgumentParser(description="Extract form fields from PDF")
    parser.add_argument("pdf_path", help="Path to PDF file")

    args = parser.parse_args()

    # Validate file exists
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Extract form fields
    result = extract_form_fields(pdf_path)

    # Check for errors
    if "error" in result:
        print(f"Error extracting forms: {result['error']}", file=sys.stderr)
        # Still output JSON with error for parsing
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Output JSON to stdout
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

