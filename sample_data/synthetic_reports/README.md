# Synthetic Reports

Synthetic medical report samples for testing and development.

## Guidelines

- All data is SYNTHETIC - no real patient data
- Reports cover various test types:
  - Complete Blood Count (CBC)
  - Comprehensive Metabolic Panel (CMP)
  - Lipid Panel
  - Thyroid Function Tests
  - Hemoglobin A1C
- Include both normal and abnormal values
- Include edge cases (borderline, missing ranges)

## File Formats

- `*.pdf` - Digital PDF samples
- `*_scanned.pdf` - Simulated scanned PDFs
- `*.jpg`, `*.png` - Image samples
- `*.docx` - Word document samples

## Naming Convention

`{test_type}_{scenario}_{format}.{ext}`

Example: `cbc_abnormal_digital.pdf`
