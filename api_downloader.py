"""
Generic API File Downloader with Base64 to PDF Conversion

A flexible, reusable implementation for downloading files from REST APIs
and converting base64-encoded content to PDF files.
"""

import os
import json
import base64
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class APIDownloader:
    """Generic downloader for fetching files from REST APIs and converting base64 to PDF."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the API downloader.

        Args:
            config_path: Path to JSON configuration file
        """
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self._setup_logging()
        self._setup_session()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)

    def _setup_logging(self):
        """Configure logging based on config settings."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))

        # Create logs directory if enabled
        if log_config.get('enabled', True):
            os.makedirs('logs', exist_ok=True)
            log_file = f"logs/download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(level=log_level, format='%(levelname)s - %(message)s')

        self.logger = logging.getLogger(__name__)

    def _setup_session(self):
        """Configure requests session with authentication and headers."""
        auth_config = self.config.get('authentication', {})

        # Set headers
        if 'headers' in auth_config:
            self.session.headers.update(auth_config['headers'])

        # Set authentication
        if auth_config.get('type') == 'basic':
            self.session.auth = (
                auth_config.get('username'),
                auth_config.get('password')
            )
        elif auth_config.get('type') == 'bearer':
            self.session.headers['Authorization'] = f"Bearer {auth_config.get('token')}"

        # Set timeout
        self.timeout = self.config.get('api', {}).get('timeout', 30)

    def fetch_file_list(self) -> List[Dict[str, Any]]:
        """
        Fetch list of files from API endpoint.

        Returns:
            List of file metadata dictionaries
        """
        api_config = self.config['api']
        list_endpoint = api_config.get('list_endpoint')

        if not list_endpoint:
            self.logger.error("No list_endpoint configured")
            return []

        try:
            self.logger.info(f"Fetching file list from {list_endpoint}")
            response = self.session.get(list_endpoint, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Extract files from response based on data_path
            data_path = api_config.get('data_path', '')
            if data_path:
                for key in data_path.split('.'):
                    data = data.get(key, [])

            self.logger.info(f"Found {len(data)} files")
            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching file list: {e}")
            return []

    def download_file(self, file_id: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Download a single file and convert to PDF if base64 encoded.

        Args:
            file_id: Unique identifier for the file
            metadata: Optional metadata about the file

        Returns:
            Path to saved file, or None if failed
        """
        api_config = self.config['api']
        download_endpoint = api_config['download_endpoint'].format(id=file_id)

        try:
            self.logger.info(f"Downloading file {file_id}")
            response = self.session.get(download_endpoint, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Extract file content and metadata
            content_field = api_config.get('content_field', 'content')
            filename_field = api_config.get('filename_field', 'filename')

            base64_content = data.get(content_field)
            filename = metadata.get(filename_field) if metadata else data.get(filename_field, f"{file_id}.pdf")

            if not base64_content:
                self.logger.warning(f"No content found for file {file_id}")
                return None

            # Convert and save file
            return self._save_file(base64_content, filename, file_id)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading file {file_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing file {file_id}: {e}")
            return None

    def _save_file(self, base64_content: str, filename: str, file_id: str) -> Optional[str]:
        """
        Decode base64 content and save to file.

        Args:
            base64_content: Base64-encoded file content
            filename: Name for the output file
            file_id: Unique identifier for the file

        Returns:
            Path to saved file, or None if failed
        """
        output_config = self.config.get('output', {})
        output_dir = output_config.get('directory', 'downloads')

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Decode base64 content
            file_bytes = base64.b64decode(base64_content)

            # Sanitize filename
            safe_filename = self._sanitize_filename(filename)
            if not safe_filename.lower().endswith('.pdf'):
                safe_filename += '.pdf'

            # Save file
            file_path = os.path.join(output_dir, safe_filename)

            # Handle duplicate filenames
            if os.path.exists(file_path):
                base, ext = os.path.splitext(safe_filename)
                file_path = os.path.join(output_dir, f"{base}_{file_id}{ext}")

            with open(file_path, 'wb') as f:
                f.write(file_bytes)

            file_size = len(file_bytes) / 1024  # KB
            self.logger.info(f"Saved {safe_filename} ({file_size:.2f} KB)")

            return file_path

        except Exception as e:
            self.logger.error(f"Error saving file {filename}: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """Remove or replace invalid characters in filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    def download_all(self, max_workers: int = 5) -> Dict[str, Any]:
        """
        Download all files using concurrent workers.

        Args:
            max_workers: Number of concurrent download threads

        Returns:
            Summary dictionary with statistics
        """
        files = self.fetch_file_list()

        if not files:
            self.logger.warning("No files to download")
            return {'total': 0, 'successful': 0, 'failed': 0}

        id_field = self.config['api'].get('id_field', 'id')
        successful = []
        failed = []

        self.logger.info(f"Starting download of {len(files)} files with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.download_file, file.get(id_field), file): file
                for file in files
            }

            for future in as_completed(future_to_file):
                file_metadata = future_to_file[future]
                file_id = file_metadata.get(id_field)

                try:
                    result = future.result()
                    if result:
                        successful.append(file_id)
                    else:
                        failed.append(file_id)
                except Exception as e:
                    self.logger.error(f"Exception for file {file_id}: {e}")
                    failed.append(file_id)

        summary = {
            'total': len(files),
            'successful': len(successful),
            'failed': len(failed),
            'failed_ids': failed
        }

        self.logger.info(f"Download complete: {summary['successful']}/{summary['total']} successful")

        return summary

    def download_by_ids(self, file_ids: List[str], max_workers: int = 5) -> Dict[str, Any]:
        """
        Download specific files by their IDs.

        Args:
            file_ids: List of file IDs to download
            max_workers: Number of concurrent download threads

        Returns:
            Summary dictionary with statistics
        """
        successful = []
        failed = []

        self.logger.info(f"Starting download of {len(file_ids)} specific files")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(self.download_file, file_id): file_id
                for file_id in file_ids
            }

            for future in as_completed(future_to_id):
                file_id = future_to_id[future]

                try:
                    result = future.result()
                    if result:
                        successful.append(file_id)
                    else:
                        failed.append(file_id)
                except Exception as e:
                    self.logger.error(f"Exception for file {file_id}: {e}")
                    failed.append(file_id)

        summary = {
            'total': len(file_ids),
            'successful': len(successful),
            'failed': len(failed),
            'failed_ids': failed
        }

        self.logger.info(f"Download complete: {summary['successful']}/{summary['total']} successful")

        return summary


def main():
    """Example usage of the API downloader."""
    import argparse

    parser = argparse.ArgumentParser(description='Download files from API and convert base64 to PDF')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--workers', type=int, default=5, help='Number of concurrent workers')
    parser.add_argument('--ids', nargs='+', help='Specific file IDs to download')

    args = parser.parse_args()

    downloader = APIDownloader(args.config)

    if args.ids:
        summary = downloader.download_by_ids(args.ids, max_workers=args.workers)
    else:
        summary = downloader.download_all(max_workers=args.workers)

    print(f"\nDownload Summary:")
    print(f"Total: {summary['total']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")

    if summary['failed_ids']:
        print(f"Failed IDs: {', '.join(map(str, summary['failed_ids']))}")


if __name__ == '__main__':
    main()
