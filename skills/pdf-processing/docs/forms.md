# PDF Form Fields and Extraction

This document explains PDF form field types, extraction techniques, and common patterns.

## PDF Form Types

### AcroForms (Form Fields)

AcroForms are the standard PDF form format. They include interactive fields that can be filled in PDF readers.

**Common Field Types:**
- **Text fields**: Single or multi-line text input
- **Checkboxes**: Boolean on/off values
- **Radio buttons**: Multiple choice with one selection
- **Dropdown lists**: Selection from predefined options
- **Buttons**: Action triggers (submit, reset)

### XFA Forms

XFA (XML Forms Architecture) is an older XML-based form format. Less common today and not fully supported by pypdf.

## Field Names and Values

Form fields have:
- **Field name**: Unique identifier (e.g., "FirstName", "Email")
- **Field value**: Current content (string, bool, or None if empty)
- **Field type**: The widget type (text, checkbox, etc.)

## Extraction Techniques

### Using pypdf

The `extract_forms.py` script uses pypdf's built-in form extraction:

```python
from pypdf import PdfReader

reader = PdfReader("form.pdf")
fields = reader.get_form_text_fields()  # Returns dict of field_name: value
```

### Handling Empty Fields

Fields may exist but be unfilled:
- Value is `None` or empty string `""`
- Check if value exists before processing
- Count filled vs total fields for completeness metrics

### Field Name Conventions

PDF creators choose field names. Common patterns:
- **Flat names**: `"Name"`, `"Email"`, `"Phone"`
- **Hierarchical**: `"Personal.Name"`, `"Contact.Email"`
- **Indexed**: `"Item[0].Name"`, `"Item[1].Name"`

## Common Extraction Challenges

### 1. No Forms in PDF

Not all PDFs have form fields. Regular PDFs with text require text extraction instead.

**Solution**: Check if `get_form_text_fields()` returns None or empty dict.

### 2. Encrypted PDFs

Password-protected PDFs cannot be read without decryption.

**Solution**: Add password support via `reader.decrypt(password)` if needed.

### 3. Scanned PDFs

Scanned images saved as PDF have no form fields or extractable text.

**Solution**: Requires OCR (Optical Character Recognition) - not covered by this skill.

### 4. Complex Field Types

Some form fields are complex (signature fields, file attachments).

**Solution**: Use `reader.get_fields()` for full field metadata including type info.

## Example: Processing Form Data

After extraction, form data often needs validation or transformation:

```python
fields = reader.get_form_text_fields()

# Validate required fields
required = ["Name", "Email"]
missing = [f for f in required if not fields.get(f)]

# Transform data
email = fields.get("Email", "").strip().lower()
phone = fields.get("Phone", "").replace("-", "").replace(" ", "")
```

## Best Practices

1. **Always check for form existence**: Not all PDFs have forms
2. **Handle None values**: Empty fields return None
3. **Validate extracted data**: Check required fields are present
4. **Provide user feedback**: Tell user how many fields found/filled
5. **Log errors**: PDF parsing can fail - capture exceptions

## Performance Notes

- Form extraction is fast (milliseconds)
- Reading large PDFs (100+ pages) may take a few seconds
- Memory usage is proportional to PDF size
- Consider chunking for batch processing of many PDFs

