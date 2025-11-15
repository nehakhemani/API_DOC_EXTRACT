# API File Downloader with Base64 to PDF Conversion

A clean, generic implementation for downloading files from REST APIs and converting base64-encoded content to PDF files.

## Features

- **Generic & Reusable**: Configuration-driven design works with any REST API
- **Concurrent Downloads**: Multi-threaded downloading with configurable workers
- **Base64 to PDF Conversion**: Automatic decoding and file saving
- **Flexible Authentication**: Supports Bearer tokens, Basic auth, and custom headers
- **Comprehensive Logging**: Detailed logs with timestamps and error tracking
- **Robust Error Handling**: Retry logic and graceful failure handling
- **Command Line Interface**: Easy-to-use CLI with argument parsing

## Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

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

## Troubleshooting

### Authentication Failures
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
- requests library

Install with:
```bash
pip install requests
```

## File Structure

```
PDF_CCL/
├── api_downloader.py          # Main downloader class
├── config.json                # Your configuration (create from example)
├── config.example.json        # Configuration template
├── README.md                  # This file
├── downloads/                 # Downloaded PDFs (created automatically)
└── logs/                      # Log files (created automatically)
```

## License

This is a generic implementation designed to be adapted for your specific API needs.

## Contributing

This is a standalone tool. Modify the code to fit your specific requirements.
