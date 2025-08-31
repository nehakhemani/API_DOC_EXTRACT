import requests
import base64
import csv
import os
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

@dataclass
class DownloadConfig:
    """Configuration for the downloader"""
    base_url: str
    headers: Dict[str, str]
    download_folder: str = "downloads"
    log_folder: str = "logs"
    max_workers: int = 5
    delay_between_batches: float = 1.0
    batch_size: int = 20
    request_timeout: int = 30
    retry_on_failure: bool = True
    max_retries: int = 3

class ConcurrentBase64Downloader:
    """
    A reusable concurrent downloader for Base64-encoded files from REST APIs.
    
    Features:
    - Concurrent downloads with configurable thread pool
    - Base64 decoding and file saving
    - Comprehensive error handling and categorization
    - Progress tracking and detailed logging
    - Resume capability (skips already downloaded files)
    - Flexible CSV input handling
    - Configurable retry logic
    """
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        
        # Thread-safe counters
        self.lock = Lock()
        self.stats = {
            'successful': 0,
            'failed': 0,
            'processed': 0,
            'skipped': 0,
            'error_types': {}
        }
        
        # Create necessary folders
        self._create_folders()
    
    def _create_folders(self):
        """Create download and log folders if they don't exist"""
        os.makedirs(self.config.download_folder, exist_ok=True)
        os.makedirs(self.config.log_folder, exist_ok=True)
    
    def get_downloaded_ids(self) -> Set[str]:
        """Get set of already downloaded IDs by scanning the download folder"""
        downloaded_ids = set()
        
        if os.path.exists(self.config.download_folder):
            for filename in os.listdir(self.config.download_folder):
                if '_' in filename:
                    id_part = filename.split('_')[0]
                    if id_part.isdigit():
                        downloaded_ids.add(id_part)
        
        return downloaded_ids
    
    def load_ids_from_csv(self, csv_file: str, id_column: str = 'ATTACHMENTID', 
                         start_line: Optional[int] = None) -> List[str]:
        """
        Load IDs from CSV file with optional starting line
        
        Args:
            csv_file: Path to CSV file
            id_column: Column name containing IDs
            start_line: Optional line number to start from (1-indexed)
        """
        ids = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for line_num, row in enumerate(csv_reader, 1):
                    if start_line and line_num < start_line:
                        continue
                    
                    attachment_id = row[id_column].strip()
                    if attachment_id and attachment_id.isdigit():
                        ids.append(attachment_id)
        
        except Exception as e:
            print(f"Error reading CSV {csv_file}: {e}")
            return []
        
        return ids
    
    def load_ids_from_list(self, id_list: List[str]) -> List[str]:
        """Load IDs from a simple list"""
        return [str(id_val).strip() for id_val in id_list if str(id_val).strip().isdigit()]
    
    def _sanitize_filename(self, filename: str, attachment_id: str) -> str:
        """Clean and sanitize filename for safe file system storage"""
        if not filename:
            return f"attachment_{attachment_id}"
        
        # Remove/replace unsafe characters
        safe_chars = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        safe_filename = safe_chars.strip()
        
        # Ensure we have a valid filename
        if not safe_filename or safe_filename == '.':
            safe_filename = f"attachment_{attachment_id}"
        
        # Limit length to avoid filesystem issues
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:190] + ext
        
        return safe_filename
    
    def _download_single_file(self, attachment_id: str, retries: int = 0) -> Tuple[str, bool, str, str]:
        """
        Download a single file with detailed error handling
        
        Returns:
            (attachment_id, success, message, error_type)
        """
        try:
            url = f"{self.config.base_url}{attachment_id}"
            response = requests.get(url, headers=self.config.headers, 
                                  timeout=self.config.request_timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains data
                if 'items' not in data or len(data['items']) == 0:
                    return attachment_id, False, "No data in response", "NO_DATA"
                
                attachment_info = data['items'][0]
                base64_data = attachment_info.get('data', '')
                filename = attachment_info.get('fullPath', attachment_info.get('fileName', ''))
                
                if not base64_data:
                    return attachment_id, False, "No base64 data", "NO_BASE64"
                
                # Generate safe filename
                safe_filename = self._sanitize_filename(filename, attachment_id)
                output_path = os.path.join(self.config.download_folder, f"{attachment_id}_{safe_filename}")
                
                # Check if file already exists
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    return attachment_id, True, f"Already exists: {safe_filename} ({file_size:,}b)", "ALREADY_EXISTS"
                
                # Decode and save file
                try:
                    file_bytes = base64.b64decode(base64_data)
                    with open(output_path, 'wb') as f:
                        f.write(file_bytes)
                    
                    return attachment_id, True, f"{safe_filename} ({len(file_bytes):,}b)", "SUCCESS"
                
                except Exception as decode_error:
                    return attachment_id, False, f"Base64 decode error: {str(decode_error)[:50]}", "DECODE_ERROR"
            
            # Handle different HTTP status codes
            elif response.status_code == 404:
                return attachment_id, False, "File not found", "NOT_FOUND"
            elif response.status_code == 500:
                return attachment_id, False, "Server error", "SERVER_ERROR"
            elif response.status_code == 401:
                return attachment_id, False, "Unauthorized", "AUTH_ERROR"
            elif response.status_code == 403:
                return attachment_id, False, "Forbidden", "FORBIDDEN"
            elif response.status_code == 429:
                return attachment_id, False, "Rate limited", "RATE_LIMITED"
            else:
                return attachment_id, False, f"HTTP {response.status_code}", f"HTTP_{response.status_code}"
        
        except requests.exceptions.Timeout:
            if self.config.retry_on_failure and retries < self.config.max_retries:
                time.sleep(2 ** retries)  # Exponential backoff
                return self._download_single_file(attachment_id, retries + 1)
            return attachment_id, False, "Request timeout", "TIMEOUT"
        
        except requests.exceptions.ConnectionError:
            if self.config.retry_on_failure and retries < self.config.max_retries:
                time.sleep(2 ** retries)  # Exponential backoff
                return self._download_single_file(attachment_id, retries + 1)
            return attachment_id, False, "Connection error", "CONNECTION_ERROR"
        
        except Exception as e:
            return attachment_id, False, f"Unexpected error: {str(e)[:50]}", "UNKNOWN_ERROR"
    
    def _update_stats(self, success: bool, error_type: str):
        """Thread-safe statistics update"""
        with self.lock:
            self.stats['processed'] += 1
            if success:
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
                self.stats['error_types'][error_type] = self.stats['error_types'].get(error_type, 0) + 1
    
    def _log_result(self, log_file: str, detailed_csv: str, attachment_id: str, 
                   success: bool, message: str, error_type: str):
        """Write result to log files"""
        timestamp_str = datetime.now().strftime('%H:%M:%S')
        status = "SUCCESS" if success else "FAILED"
        
        # Text log
        log_entry = f"{timestamp_str},{attachment_id},{status},{message}\\n"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # CSV log
        with open(detailed_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([attachment_id, status, error_type, message, timestamp_str])
    
    def download_from_csv(self, csv_file: str, id_column: str = 'ATTACHMENTID', 
                         start_line: Optional[int] = None, resume: bool = True) -> Dict:
        """
        Download files from CSV input
        
        Args:
            csv_file: Path to CSV file
            id_column: Column name containing attachment IDs
            start_line: Optional line number to start from
            resume: Whether to skip already downloaded files
        """
        return self._download_batch(
            ids=self.load_ids_from_csv(csv_file, id_column, start_line),
            source_description=f"CSV: {csv_file} (line {start_line or 1}+)",
            resume=resume
        )
    
    def download_from_list(self, id_list: List[str], source_description: str = "ID List", 
                          resume: bool = True) -> Dict:
        """
        Download files from list of IDs
        
        Args:
            id_list: List of attachment IDs
            source_description: Description for logging
            resume: Whether to skip already downloaded files
        """
        return self._download_batch(
            ids=self.load_ids_from_list(id_list),
            source_description=source_description,
            resume=resume
        )
    
    def _download_batch(self, ids: List[str], source_description: str, resume: bool) -> Dict:
        """Core batch download logic"""
        if not ids:
            print("No IDs to process!")
            return self._get_stats_summary()
        
        # Filter already downloaded if resume is enabled
        if resume:
            downloaded_ids = self.get_downloaded_ids()
            original_count = len(ids)
            ids = [aid for aid in ids if aid not in downloaded_ids]
            skipped = original_count - len(ids)
            self.stats['skipped'] = skipped
            
            if skipped > 0:
                print(f"Resuming: skipped {skipped} already downloaded files")
        
        total = len(ids)
        if total == 0:
            print("No new files to process!")
            return self._get_stats_summary()
        
        # Setup logging
        timestamp = datetime.now().strftime('%H%M%S')
        log_file = f"{self.config.log_folder}/download_log_{timestamp}.txt"
        detailed_csv = f"{self.config.log_folder}/download_detailed_{timestamp}.csv"
        
        self._initialize_logs(log_file, detailed_csv, source_description, total)
        
        print(f"\\n=== STARTING CONCURRENT DOWNLOAD ===")
        print(f"Source: {source_description}")
        print(f"Files to download: {total:,}")
        print(f"Threads: {self.config.max_workers}")
        print(f"Batch size: {self.config.batch_size}")
        print(f"Log files: {log_file}, {detailed_csv}")
        print()
        
        start_time = time.time()
        
        # Process in batches to avoid overwhelming the server
        for i in range(0, total, self.config.batch_size):
            batch = ids[i:i + self.config.batch_size]
            batch_num = i // self.config.batch_size + 1
            total_batches = (total - 1) // self.config.batch_size + 1
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)...")
            
            # Download batch concurrently
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_id = {executor.submit(self._download_single_file, aid): aid for aid in batch}
                
                for future in as_completed(future_to_id):
                    attachment_id, success, message, error_type = future.result()
                    
                    # Update statistics
                    self._update_stats(success, error_type)
                    
                    # Log result
                    self._log_result(log_file, detailed_csv, attachment_id, success, message, error_type)
                    
                    # Console output
                    status_text = "SUCCESS" if success else "FAILED"
                    print(f"  {status_text} {attachment_id}: {message}")
            
            # Progress report
            self._print_progress(total, start_time)
            
            # Delay between batches (except last batch)
            if i + self.config.batch_size < total:
                time.sleep(self.config.delay_between_batches)
        
        # Final summary
        duration = time.time() - start_time
        self._print_final_summary(duration, log_file, detailed_csv)
        self._write_final_log_summary(log_file, duration)
        
        return self._get_stats_summary()
    
    def _initialize_logs(self, log_file: str, detailed_csv: str, source: str, total: int):
        """Initialize log files with headers"""
        # Text log header
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== CONCURRENT BASE64 DOWNLOADER LOG ===\\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Source: {source}\\n")
            f.write(f"Files to process: {total:,}\\n")
            f.write(f"Config: {self.config.max_workers} threads, {self.config.batch_size} batch size, {self.config.delay_between_batches}s delay\\n")
            f.write(f"=== DOWNLOAD RESULTS ===\\n")
        
        # CSV header
        with open(detailed_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ATTACHMENT_ID', 'STATUS', 'ERROR_TYPE', 'MESSAGE', 'TIMESTAMP'])
    
    def _print_progress(self, total: int, start_time: float):
        """Print progress update"""
        if self.stats['processed'] % 50 == 0 or self.stats['processed'] == total:
            elapsed = time.time() - start_time
            rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
            eta = (total - self.stats['processed']) / rate if rate > 0 else 0
            
            print(f"\\nProgress: {self.stats['processed']:,}/{total:,} ({self.stats['processed']/total*100:.1f}%)")
            print(f"Speed: {rate:.1f} files/sec | ETA: {eta/60:.1f} min")
            print(f"Success: {self.stats['successful']:,} | Failed: {self.stats['failed']:,}")
            if self.stats['skipped'] > 0:
                print(f"Skipped: {self.stats['skipped']:,}")
            print()
    
    def _print_final_summary(self, duration: float, log_file: str, detailed_csv: str):
        """Print final download summary"""
        print(f"\\n=== DOWNLOAD COMPLETE ===")
        print(f"Duration: {duration/60:.1f} minutes")
        print(f"Files processed: {self.stats['processed']:,}")
        print(f"Successfully downloaded: {self.stats['successful']:,}")
        print(f"Failed: {self.stats['failed']:,}")
        if self.stats['skipped'] > 0:
            print(f"Skipped (already downloaded): {self.stats['skipped']:,}")
        
        if self.stats['processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['processed']) * 100
            print(f"Success rate: {success_rate:.2f}%")
        
        if self.stats['error_types']:
            print(f"\\nError breakdown:")
            for error_type, count in sorted(self.stats['error_types'].items(), 
                                          key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count:,} files")
        
        print(f"\\nLog files:")
        print(f"  Text log: {log_file}")
        print(f"  Detailed CSV: {detailed_csv}")
    
    def _write_final_log_summary(self, log_file: str, duration: float):
        """Write final summary to log file"""
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\\n=== FINAL SUMMARY ===\\n")
            f.write(f"Duration: {duration/60:.1f} minutes\\n")
            f.write(f"Processed: {self.stats['processed']:,}\\n")
            f.write(f"Success: {self.stats['successful']:,}\\n")
            f.write(f"Failed: {self.stats['failed']:,}\\n")
            f.write(f"Skipped: {self.stats['skipped']:,}\\n")
            
            if self.stats['processed'] > 0:
                success_rate = (self.stats['successful'] / self.stats['processed']) * 100
                f.write(f"Success rate: {success_rate:.2f}%\\n")
            
            if self.stats['error_types']:
                f.write(f"\\nError breakdown:\\n")
                for error_type, count in sorted(self.stats['error_types'].items(), 
                                              key=lambda x: x[1], reverse=True):
                    f.write(f"  {error_type}: {count:,}\\n")
    
    def _get_stats_summary(self) -> Dict:
        """Get current statistics as dictionary"""
        return {
            'processed': self.stats['processed'],
            'successful': self.stats['successful'],
            'failed': self.stats['failed'],
            'skipped': self.stats['skipped'],
            'success_rate': (self.stats['successful'] / self.stats['processed'] * 100) if self.stats['processed'] > 0 else 0,
            'error_types': dict(self.stats['error_types'])
        }

def create_autotask_config() -> DownloadConfig:
    """Create configuration for Autotask API (example)"""
    return DownloadConfig(
        base_url="https://webservices6.autotask.net/atservicesrest/v1.0/CompanyAttachments/",
        headers={
            "ApiIntegrationcode": "YOUR_INTEGRATION_CODE",
            "UserName": "YOUR_USERNAME",
            "Secret": "YOUR_SECRET",
            "Content-Type": "application/json"
        },
        download_folder="downloaded_pdfs",
        log_folder="logs",
        max_workers=5,
        delay_between_batches=1.0,
        batch_size=20,
        request_timeout=30
    )

# Example usage functions
def download_from_csv_example():
    """Example: Download from CSV file"""
    config = create_autotask_config()
    downloader = ConcurrentBase64Downloader(config)
    
    # Download from CSV starting at specific line
    results = downloader.download_from_csv(
        csv_file='your_file.csv',
        id_column='ATTACHMENTID',
        start_line=1000,  # Optional: start from specific line
        resume=True       # Skip already downloaded files
    )
    
    print(f"Download completed with {results['success_rate']:.1f}% success rate")

def download_from_list_example():
    """Example: Download from list of IDs"""
    config = create_autotask_config()
    downloader = ConcurrentBase64Downloader(config)
    
    # Download specific IDs
    id_list = ["123456", "789012", "345678"]
    results = downloader.download_from_list(
        id_list=id_list,
        source_description="Manual ID List",
        resume=True
    )
    
    print(f"Download completed: {results['successful']}/{results['processed']} files")

def custom_api_example():
    """Example: Configure for different API"""
    config = DownloadConfig(
        base_url="https://api.example.com/files/",
        headers={
            "Authorization": "Bearer YOUR_TOKEN",
            "Content-Type": "application/json"
        },
        download_folder="custom_downloads",
        max_workers=3,
        batch_size=10,
        delay_between_batches=2.0
    )
    
    downloader = ConcurrentBase64Downloader(config)
    results = downloader.download_from_list(["file1", "file2", "file3"])
    
    return results

if __name__ == "__main__":
    print("Concurrent Base64 Downloader - Ready for use!")
    print("\\nExample usage:")
    print("1. Configure your API settings in create_autotask_config()")
    print("2. Use download_from_csv() or download_from_list()")
    print("3. Check the generated log files for detailed results")