# API File Downloader & Document Validator

A comprehensive toolkit for downloading files from REST APIs, converting base64 to PDF, and validating document content.

## Features

### API Downloader
- **Generic & Reusable**: Configuration-driven design works with any REST API
- **Concurrent Downloads**: Multi-threaded downloading with configurable workers
- **Base64 to PDF Conversion**: Automatic decoding and file saving
- **Flexible Authentication**: Supports Bearer tokens, Basic auth, and custom headers
- **Comprehensive Logging**: Detailed logs with timestamps and error tracking
- **Robust Error Handling**: Retry logic and graceful failure handling

### Document Validator
- **Signature Detection**: Identifies if documents are signed based on keywords and patterns
- **Signatory Classification**: Separates customer vs company signatures
- **Date Extraction**: Finds and extracts signing dates from documents
- **Customer Name Extraction**: Identifies customer/client names from filenames and content
- **Agreement Type Detection**: Classifies documents by agreement type (Business, NDA, License, etc.)
- **OCR Support**: Processes scanned/image-based PDFs using Tesseract OCR
- **Batch Processing**: Validate entire directories of PDFs at once
- **JSON Export**: Save validation results to structured JSON files

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
# For API downloader
pip install requests

# For document validator
pip install PyPDF2 pdfplumber

# For OCR support (scanned PDFs)
pip install pdf2image pytesseract Pillow
```

**Note for Scanned PDFs**: If you need to process scanned/image-based PDFs, additional system dependencies are required (Poppler and Tesseract OCR). See **[OCR_SETUP.md](OCR_SETUP.md)** for detailed installation instructions.

### 2. Create Configuration File

Copy `config.example.json` to `config.json` and update with your API details:

```json
{
  "api": {
    "base_url": "https://api.example.com",
    "list_endpoint": "https://api.example.com/files",
    "download_endpoint": "https://api.example.com/files/{id}",
    "timeout": 30,
    "id_field": "id",
    "content_field": "base64Content",
    "filename_field": "fileName",
    "data_path": "data.items"
  },
  "authentication": {
    "type": "bearer",
    "token": "your_api_token_here",
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "output": {
    "directory": "downloads"
  },
  "logging": {
    "enabled": true,
    "level": "INFO"
  }
}
```

### 3. Run the Downloader

```bash
# Download all files
python api_downloader.py

# Download with custom config
python api_downloader.py --config my_config.json

# Download with more workers
python api_downloader.py --workers 10

# Download specific files by ID
python api_downloader.py --ids 123 456 789
```

## Configuration Guide

### API Configuration

- **base_url**: Base URL of your API
- **list_endpoint**: Endpoint to fetch list of available files (optional)
- **download_endpoint**: Endpoint template for downloading files (use `{id}` placeholder)
- **timeout**: Request timeout in seconds (default: 30)
- **id_field**: JSON field name containing file ID (default: "id")
- **content_field**: JSON field name containing base64 content (default: "content")
- **filename_field**: JSON field name containing filename (default: "filename")
- **data_path**: Dot-notation path to extract file list from nested JSON (e.g., "data.items")

### Authentication Types

**Bearer Token:**
```json
{
  "authentication": {
    "type": "bearer",
    "token": "your_token_here"
  }
}
```

**Basic Authentication:**
```json
{
  "authentication": {
    "type": "basic",
    "username": "your_username",
    "password": "your_password"
  }
}
```

**Custom Headers Only:**
```json
{
  "authentication": {
    "headers": {
      "X-API-Key": "your_api_key",
      "Custom-Header": "value"
    }
  }
}
```

### Output Configuration

- **directory**: Directory where downloaded PDFs will be saved (default: "downloads")

### Logging Configuration

- **enabled**: Enable/disable file logging (default: true)
- **level**: Logging level - DEBUG, INFO, WARNING, ERROR (default: "INFO")

## Usage Examples

### Python API Usage

```python
from api_downloader import APIDownloader

# Initialize with config
downloader = APIDownloader('config.json')

# Download all files
summary = downloader.download_all(max_workers=5)
print(f"Downloaded {summary['successful']}/{summary['total']} files")

# Download specific files
file_ids = ['123', '456', '789']
summary = downloader.download_by_ids(file_ids, max_workers=3)

# Download single file
file_path = downloader.download_file('123')
if file_path:
    print(f"File saved to: {file_path}")
```

### Command Line Usage

```bash
# Basic download all
python api_downloader.py

# Custom configuration
python api_downloader.py --config production_config.json

# Increase concurrency
python api_downloader.py --workers 20

# Download specific files
python api_downloader.py --ids 110581 111125 111749

# Combine options
python api_downloader.py --config prod.json --workers 10 --ids 123 456
```

## API Response Format

The downloader expects your API to return JSON responses in this format:

**For list endpoint:**
```json
{
  "data": {
    "items": [
      {
        "id": "123",
        "fileName": "document.pdf"
      }
    ]
  }
}
```

**For download endpoint:**
```json
{
  "id": "123",
  "fileName": "document.pdf",
  "base64Content": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC..."
}
```

Adjust the `data_path`, `id_field`, `content_field`, and `filename_field` in your config to match your API's structure.

## Features in Detail

### Automatic File Naming

- Uses filename from API metadata
- Automatically adds `.pdf` extension if missing
- Sanitizes filenames (removes invalid characters)
- Handles duplicate filenames by appending file ID

### Error Handling

- Connection errors with detailed logging
- HTTP errors (404, 401, 500, etc.)
- Base64 decoding errors
- Timeout handling
- Missing content warnings

### Concurrent Processing

- ThreadPoolExecutor for parallel downloads
- Configurable number of workers
- Progress tracking for each file
- Graceful handling of failures in concurrent execution

### Logging

All operations are logged with:
- Timestamps
- Log levels (INFO, WARNING, ERROR)
- Detailed error messages
- File-based logs (when enabled)
- Console output for real-time monitoring

Log files are saved in `logs/download_YYYYMMDD_HHMMSS.log`

## Performance Tuning

### High Performance (Fast API)
```bash
python api_downloader.py --workers 20
```

### Conservative (Rate-Limited API)
```bash
python api_downloader.py --workers 1
```

Update timeout in config for slow APIs:
```json
{
  "api": {
    "timeout": 60
  }
}
```

## Document Validator

The Document Validator analyzes PDF files to extract key information and validate document properties.

### Features

The validator can extract:
1. **Signature Status**: Detects if document is signed (based on keywords like "signature", "signed by", "electronically signed")
2. **Signing Date**: Extracts the date when document was signed
3. **Customer Name**: Identifies customer/client name from filename or document content
4. **Agreement Type**: Classifies the document (Business Agreement, NDA, License Agreement, etc.)

### Usage Examples

**Validate a single PDF:**
```bash
python document_validator.py "path/to/document.pdf"
```

**Validate an entire directory:**
```bash
python document_validator.py downloads/
```

**Save results to JSON:**
```bash
# Single file
python document_validator.py "document.pdf" --output results.json

# Directory
python document_validator.py downloads/ --output validation_results.json
```

**Adjust logging level:**
```bash
python document_validator.py "document.pdf" --log-level DEBUG
```

### Example Output

```
============================================================
Document: 46367_FIDELITY LIFE ASSURANCE CO LTD_General Business Agreement.pdf
============================================================

Agreement Type: Business Agreement (medium confidence)
Customer Name: Company Life Assurance Co Ltd
Signed: No (low confidence)
Signing Date: 10/07/2024

Dates Found: 10/07/2024

============================================================
```

### Programmatic Usage

```python
from document_validator import DocumentValidator

# Initialize validator
validator = DocumentValidator(log_level="INFO")

# Validate single document
result = validator.validate_document("path/to/document.pdf")

# Access extracted information
print(f"Agreement Type: {result['agreement_type']['type']}")
print(f"Customer: {result['customer_name']}")
print(f"Is Signed: {result['signature']['is_signed']}")
print(f"Signing Date: {result['signing_date']}")

# Validate entire directory
results = validator.validate_directory("downloads/", output_file="results.json")

# Process results
for doc in results:
    if doc['signature']['is_signed']:
        print(f"{doc['filename']} is signed on {doc['signing_date']}")
```

### JSON Output Format

```json
{
  "filename": "document.pdf",
  "file_path": "/path/to/document.pdf",
  "status": "success",
  "signature": {
    "is_signed": true,
    "confidence": "high",
    "indicators_found": 3,
    "signature_indicators": ["signature", "signed by", "date signed"]
  },
  "signing_date": "10/07/2024",
  "customer_name": "Customer Corporation",
  "agreement_type": {
    "type": "Business Agreement",
    "confidence": "high"
  },
  "extracted_dates": ["10/07/2024", "15/08/2024"],
  "text_length": 12458,
  "analyzed_at": "2025-11-16T12:30:45"
}
```

### Supported Agreement Types

The validator can detect these agreement types:
- Business Agreement
- Service Agreement
- License Agreement
- Non-Disclosure Agreement (NDA)
- Sales Agreement
- Employment Agreement
- Partnership Agreement
- Lease Agreement
- Master Agreement (MSA)

### How It Works

1. **Text Extraction**: Uses pdfplumber (preferred) or PyPDF2 to extract text from PDF
2. **Pattern Matching**: Applies regex patterns to identify signatures, dates, and agreement types
3. **Filename Parsing**: Extracts customer names from structured filenames (e.g., `ID_CUSTOMERNAME_Type.pdf`)
4. **Confidence Scoring**: Assigns confidence levels based on number of matches found
5. **Results Compilation**: Combines all extracted data into structured output

### Filename Convention

For best results, use this filename pattern:
```
{ID}_{CUSTOMER_NAME}_{AGREEMENT_TYPE}.pdf
```

Example: `46367_FIDELITY LIFE ASSURANCE CO LTD_General Business Agreement.pdf`

The validator will extract:
- ID: 46367
- Customer: FIDELITY LIFE ASSURANCE CO LTD
- Type: General Business Agreement

## Troubleshooting

### Document Validator Issues

#### Cannot Extract Text from Scanned PDF
If you see: `Could not extract text from PDF` for a scanned document:

1. The PDF is likely image-based and requires OCR
2. Install OCR dependencies:
   ```bash
   pip install pdf2image pytesseract Pillow
   ```
3. Install system dependencies (Poppler and Tesseract)
   - See **[OCR_SETUP.md](OCR_SETUP.md)** for detailed instructions
4. Common errors:
   - `Unable to get page count. Is poppler installed` → Install Poppler
   - `tesseract is not installed` → Install Tesseract OCR
   - See OCR_SETUP.md for troubleshooting

#### Signature Not Detected
- Check if document contains signature keywords or role/title indicators
- For scanned signatures (images), ensure OCR is working properly
- Verify the document actually contains text (not just images)

### API Downloader Issues

#### Authentication Failures
- Verify your token/credentials in config
- Check token hasn't expired
- Ensure correct authentication type
- Verify custom headers if used

### No Files Downloaded
- Check `list_endpoint` is correct
- Verify `data_path` matches your API structure
- Review logs for API errors
- Test API endpoints manually with curl/Postman

### Base64 Decode Errors
- Verify `content_field` matches your API response
- Check that content is valid base64
- Ensure API returns complete content

### Timeout Errors
- Increase timeout in config
- Reduce number of workers
- Check network connectivity
- Verify API is responsive

## Requirements

- Python 3.7+
- requests (for API downloader)
- PyPDF2 (for document validator)
- pdfplumber (for document validator)

Install all dependencies:
```bash
pip install -r requirements.txt
```

## File Structure

```
PDF_CCL/
├── api_downloader.py          # API file downloader
├── document_validator.py      # PDF document validator
├── config.json                # Your configuration (create from example)
├── config.example.json        # Configuration template
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── downloads/                 # Downloaded PDFs (created automatically)
└── logs/                      # Log files (created automatically)
```

## License

This is a generic implementation designed to be adapted for your specific API needs.

## Contributing

This is a standalone tool. Modify the code to fit your specific requirements.
