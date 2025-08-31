# Concurrent Base64 Downloader

A powerful, reusable Python tool for concurrent downloading and decoding of Base64-encoded files from REST APIs.

## Features

- **Concurrent Downloads**: Multi-threaded downloading with configurable thread pools
- **Base64 Decoding**: Automatic decoding and file saving
- **Resume Capability**: Skip already downloaded files automatically
- **Comprehensive Logging**: Detailed logs with error categorization
- **Flexible Input**: Support for CSV files or direct ID lists
- **Error Handling**: Robust error handling with retry logic
- **Rate Limiting**: Built-in delays and batch processing to respect API limits
- **Configurable**: Easy configuration via JSON files or code

## Quick Start

### 1. Setup Configuration

Create a `config.json` file with your API settings:

```json
{
  "your_api": {
    "base_url": "https://api.example.com/files/",
    "headers": {
      "Authorization": "Bearer YOUR_TOKEN",
      "Content-Type": "application/json"
    },
    "settings": {
      "download_folder": "downloads",
      "log_folder": "logs",
      "max_workers": 5,
      "delay_between_batches": 1.0,
      "batch_size": 20,
      "request_timeout": 30
    }
  }
}
```

### 2. Basic Usage

```python
from concurrent_base64_downloader import ConcurrentBase64Downloader, DownloadConfig
import json

# Load configuration
with open('config.json', 'r') as f:
    config_data = json.load(f)

api_config = config_data['your_api']
config = DownloadConfig(
    base_url=api_config['base_url'],
    headers=api_config['headers'],
    **api_config['settings']
)

# Create downloader
downloader = ConcurrentBase64Downloader(config)

# Download from CSV
results = downloader.download_from_csv(
    csv_file='your_file.csv',
    id_column='ID_COLUMN',
    resume=True
)

print(f"Downloaded {results['successful']} files with {results['success_rate']:.1f}% success rate")
```

## Usage Examples

### Download from CSV File

```python
# Download all files from CSV
results = downloader.download_from_csv(
    csv_file='data.csv',
    id_column='ATTACHMENT_ID',
    resume=True  # Skip already downloaded
)

# Resume from specific line
results = downloader.download_from_csv(
    csv_file='data.csv',
    id_column='ATTACHMENT_ID',
    start_line=1000,
    resume=True
)
```

### Download Specific IDs

```python
# Download specific files
id_list = ["123", "456", "789"]
results = downloader.download_from_list(
    id_list=id_list,
    source_description="Missing Files",
    resume=True
)
```

### Custom Configuration

```python
# Create custom configuration in code
custom_config = DownloadConfig(
    base_url="https://api.custom.com/files/",
    headers={"Authorization": "Bearer token"},
    download_folder="custom_downloads",
    max_workers=10,
    batch_size=50
)

downloader = ConcurrentBase64Downloader(custom_config)
```

## Configuration Options

### DownloadConfig Parameters

- `base_url`: API endpoint URL (without the ID parameter)
- `headers`: HTTP headers dict (authentication, content-type, etc.)
- `download_folder`: Where to save downloaded files (default: "downloads")
- `log_folder`: Where to save log files (default: "logs")
- `max_workers`: Number of concurrent threads (default: 5)
- `delay_between_batches`: Seconds to wait between batches (default: 1.0)
- `batch_size`: Number of files per batch (default: 20)
- `request_timeout`: HTTP request timeout in seconds (default: 30)
- `retry_on_failure`: Whether to retry failed requests (default: True)
- `max_retries`: Maximum number of retries (default: 3)

## Performance Tuning

### High Performance
```python
config.max_workers = 10
config.batch_size = 50
config.delay_between_batches = 0.5
```

### Conservative (API-friendly)
```python
config.max_workers = 1
config.batch_size = 5
config.delay_between_batches = 5.0
```

## Output Files

The downloader creates several output files:

### Downloaded Files
- Saved in `download_folder` with format: `{id}_{filename}`
- Base64 content is automatically decoded to binary

### Log Files
- `download_log_HHMMSS.txt`: Human-readable progress log
- `download_detailed_HHMMSS.csv`: Machine-readable detailed results

### Log Columns (CSV)
- `ATTACHMENT_ID`: The file ID
- `STATUS`: SUCCESS or FAILED
- `ERROR_TYPE`: Category of error (if failed)
- `MESSAGE`: Detailed message
- `TIMESTAMP`: When the download was attempted

## Error Types

The downloader categorizes errors for analysis:

- `SUCCESS`: File downloaded successfully
- `ALREADY_EXISTS`: File was already downloaded
- `NO_DATA`: API returned no data
- `NO_BASE64`: Response contained no Base64 content
- `NOT_FOUND`: HTTP 404 - File not found
- `SERVER_ERROR`: HTTP 500 - Server error
- `AUTH_ERROR`: HTTP 401 - Authentication failed
- `FORBIDDEN`: HTTP 403 - Access denied
- `RATE_LIMITED`: HTTP 429 - Too many requests
- `TIMEOUT`: Request timed out
- `CONNECTION_ERROR`: Network connection failed
- `DECODE_ERROR`: Base64 decoding failed
- `UNKNOWN_ERROR`: Unexpected error

## API Requirements

Your API should:

1. Accept GET requests to `{base_url}{id}`
2. Return JSON response with structure:
   ```json
   {
     "items": [
       {
         "data": "base64_encoded_content_here",
         "fullPath": "filename.pdf",
         "fileName": "filename.pdf"  // alternative to fullPath
       }
     ]
   }
   ```

## Resume Functionality

The downloader automatically detects already downloaded files by:
1. Scanning the download folder for files matching pattern `{id}_*`
2. Extracting the ID from the filename
3. Skipping those IDs during download

This allows you to safely resume interrupted downloads.

## Best Practices

1. **Start Conservative**: Begin with low `max_workers` and `batch_size`
2. **Monitor Logs**: Check error types to understand API behavior
3. **Use Resume**: Always enable resume functionality
4. **Respect Rate Limits**: Adjust delays based on API requirements
5. **Test First**: Try with a small subset before bulk downloads

## Example Scripts

See `example_usage.py` for comprehensive examples including:
- Basic CSV download
- Resume from specific line
- Retry missing files
- Custom API configurations
- Performance optimization
- Error analysis

## Troubleshooting

### Common Issues

**High Failure Rate**
- Increase `delay_between_batches`
- Reduce `max_workers` and `batch_size`
- Check API rate limits

**Slow Downloads**
- Increase `max_workers` (if API allows)
- Reduce `delay_between_batches`
- Increase `batch_size`

**Authentication Errors**
- Verify headers in config
- Check token expiration
- Confirm API permissions

**Files Not Downloading**
- Check `base_url` format
- Verify API response structure
- Review error types in logs

## Requirements

- Python 3.7+
- `requests` library
- Standard library modules: `csv`, `json`, `os`, `time`, `datetime`, `concurrent.futures`, `threading`, `base64`

## Installation

```bash
pip install requests
```

Then simply copy the `concurrent_base64_downloader.py` file to your project.