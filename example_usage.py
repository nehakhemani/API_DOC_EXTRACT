#!/usr/bin/env python3
"""
Example usage of the Concurrent Base64 Downloader

This file demonstrates various ways to use the downloader for different scenarios.
"""

import json
from concurrent_base64_downloader import ConcurrentBase64Downloader, DownloadConfig

def load_config_from_file(config_file: str, api_name: str) -> DownloadConfig:
    """Load configuration from JSON file"""
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    if api_name not in config_data:
        raise ValueError(f"API configuration '{api_name}' not found in {config_file}")
    
    api_config = config_data[api_name]
    
    return DownloadConfig(
        base_url=api_config['base_url'],
        headers=api_config['headers'],
        **api_config['settings']
    )

def example_1_download_from_csv():
    """Example 1: Download all files from a CSV"""
    print("=== Example 1: Download from CSV ===")
    
    # Load configuration from file
    config = load_config_from_file('config.json', 'autotask_api')
    downloader = ConcurrentBase64Downloader(config)
    
    # Download from CSV file
    results = downloader.download_from_csv(
        csv_file='2025-08-27 5_04pm.csv',
        id_column='ATTACHMENTID',
        resume=True  # Skip already downloaded files
    )
    
    print(f"Results: {results}")

def example_2_download_from_line():
    """Example 2: Resume download from specific line in CSV"""
    print("=== Example 2: Resume from specific line ===")
    
    config = load_config_from_file('config.json', 'autotask_api')
    downloader = ConcurrentBase64Downloader(config)
    
    # Resume from line 5000 in CSV
    results = downloader.download_from_csv(
        csv_file='2025-08-27 5_04pm.csv',
        id_column='ATTACHMENTID',
        start_line=5000,
        resume=True
    )
    
    print(f"Download from line 5000 completed: {results}")

def example_3_download_specific_ids():
    """Example 3: Download specific list of IDs"""
    print("=== Example 3: Download specific IDs ===")
    
    config = load_config_from_file('config.json', 'autotask_api')
    downloader = ConcurrentBase64Downloader(config)
    
    # Download specific files
    missing_ids = ["123456", "789012", "345678", "567890"]
    
    results = downloader.download_from_list(
        id_list=missing_ids,
        source_description="Retry Missing Files",
        resume=True
    )
    
    print(f"Specific IDs download: {results}")

def example_4_custom_api():
    """Example 4: Use with different API"""
    print("=== Example 4: Custom API Configuration ===")
    
    # Create custom configuration
    custom_config = DownloadConfig(
        base_url="https://api.mycompany.com/documents/",
        headers={
            "Authorization": "Bearer your-token-here",
            "Content-Type": "application/json",
            "X-API-Version": "v1"
        },
        download_folder="custom_downloads",
        log_folder="custom_logs",
        max_workers=3,
        batch_size=10,
        delay_between_batches=1.5,
        request_timeout=60
    )
    
    downloader = ConcurrentBase64Downloader(custom_config)
    
    # Download from custom source
    document_ids = ["doc1", "doc2", "doc3"]
    results = downloader.download_from_list(
        id_list=document_ids,
        source_description="Custom API Documents"
    )
    
    print(f"Custom API download: {results}")

def example_5_high_performance():
    """Example 5: High-performance configuration"""
    print("=== Example 5: High Performance Setup ===")
    
    # Load base config and modify for high performance
    config = load_config_from_file('config.json', 'autotask_api')
    
    # Override settings for high performance
    config.max_workers = 10      # More concurrent threads
    config.batch_size = 50       # Larger batches
    config.delay_between_batches = 0.5  # Shorter delays
    config.request_timeout = 15  # Shorter timeout
    
    downloader = ConcurrentBase64Downloader(config)
    
    # Download with high performance settings
    results = downloader.download_from_csv(
        csv_file='2025-08-27 5_04pm.csv',
        id_column='ATTACHMENTID',
        resume=True
    )
    
    print(f"High performance download: {results}")

def example_6_conservative_settings():
    """Example 6: Conservative settings for sensitive APIs"""
    print("=== Example 6: Conservative Settings ===")
    
    config = load_config_from_file('config.json', 'autotask_api')
    
    # Override for conservative approach
    config.max_workers = 1       # Single thread
    config.batch_size = 5        # Small batches
    config.delay_between_batches = 5.0  # Long delays
    config.request_timeout = 60  # Long timeout
    config.max_retries = 5       # More retries
    
    downloader = ConcurrentBase64Downloader(config)
    
    # List of problematic IDs that need careful handling
    problematic_ids = ["error_id_1", "error_id_2", "error_id_3"]
    
    results = downloader.download_from_list(
        id_list=problematic_ids,
        source_description="Problematic Files - Conservative Mode",
        resume=True
    )
    
    print(f"Conservative download: {results}")

def example_7_analyze_missing_files():
    """Example 7: Analyze and retry missing files"""
    print("=== Example 7: Analyze Missing Files ===")
    
    config = load_config_from_file('config.json', 'autotask_api')
    downloader = ConcurrentBase64Downloader(config)
    
    # First, get all IDs from CSV
    all_ids = downloader.load_ids_from_csv('2025-08-27 5_04pm.csv', 'ATTACHMENTID')
    print(f"Total IDs in CSV: {len(all_ids):,}")
    
    # Get already downloaded files
    downloaded_ids = downloader.get_downloaded_ids()
    print(f"Already downloaded: {len(downloaded_ids):,}")
    
    # Find missing files
    missing_ids = [aid for aid in all_ids if aid not in downloaded_ids]
    print(f"Missing files: {len(missing_ids):,}")
    
    if missing_ids:
        # Retry missing files with conservative settings
        results = downloader.download_from_list(
            id_list=missing_ids,
            source_description=f"Retry {len(missing_ids)} Missing Files",
            resume=False  # Don't skip since we know they're missing
        )
        
        print(f"Retry results: {results}")
    else:
        print("No missing files found!")

def run_all_examples():
    """Run all examples (commented out the ones that require actual data)"""
    print("Concurrent Base64 Downloader - Usage Examples")
    print("=" * 50)
    
    # Uncomment the examples you want to run:
    
    # example_1_download_from_csv()
    # example_2_download_from_line()
    # example_3_download_specific_ids()
    example_4_custom_api()
    # example_5_high_performance()
    # example_6_conservative_settings()
    # example_7_analyze_missing_files()

if __name__ == "__main__":
    run_all_examples()