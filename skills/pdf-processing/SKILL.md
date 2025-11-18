---
name: pdf-processing
description: Extract text, tables, and form fields from PDF documents. Use when user mentions PDFs, forms, or document extraction.
---

# PDF Processing Skill

This skill provides tools for extracting structured data from PDF files, including form fields, text content, and metadata. Useful for processing filled forms, extracting data from documents, and analyzing PDF structure.

## When to Use This Skill

Use this skill when the user:
- Mentions PDF files or documents
- Wants to extract form fields or form data
- Needs text content from PDFs
- Wants to analyze PDF structure or metadata
- Has fillable PDF forms with data to extract

## Available Scripts

### extract_forms.py

Extracts form field data from fillable PDF files.

**Usage:**
```bash
python3 /skills/pdf-processing/scripts/extract_forms.py <pdf_path>
```

**Arguments:**
- `pdf_path`: Path to the PDF file with form fields

**Output:** JSON object with form field names and values

**Example:**
```bash
# Extract all form fields from a PDF
python3 /skills/pdf-processing/scripts/extract_forms.py /data/sample_form.pdf
```

**Output format:**
```json
{
  "fields": {
    "Name": "John Doe",
    "Email": "john@example.com",
    "Address": "123 Main St"
  },
  "metadata": {
    "total_fields": 3,
    "filled_fields": 3
  }
}
```

## Supporting Documentation

For more details on PDF form structure and field types, see:
- `/skills/pdf-processing/docs/forms.md` - PDF form field types and extraction details

## Best Practices

1. **Check if PDF has forms**: Not all PDFs have form fields - script will indicate if no forms found
2. **Handle empty fields**: Some fields may be present but unfilled (null values)
3. **Text extraction**: For non-form PDFs, use pypdf's text extraction directly
4. **Error handling**: PDFs may be encrypted or corrupted - check error messages in stderr

## Example Workflow

User asks: "What information is in the sample form PDF?"

1. You: Verify file exists with `ls /data/`
2. You: Run `execute("python3 /skills/pdf-processing/scripts/extract_forms.py /data/sample_form.pdf")`
3. You: Parse JSON output
4. You: Present extracted fields to user in a readable format

## Limitations

- Only works with fillable PDF forms (AcroForms)
- Does not extract from scanned images (would need OCR)
- Complex table extraction may require additional tools
- Encrypted PDFs require password (not currently supported)

## Notes

- Scripts use pypdf library for PDF parsing
- All scripts output JSON to stdout
- Error messages go to stderr
- Form field names are defined by PDF creator

