"""
Batch Document Processor

Processes multiple PDF and Word documents and exports results to CSV and JSON.
Extracts: signatures, dates, pricing, customer names, agreement types, etc.
Supports: PDF, DOCX
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

# Setup PATH for OCR tools
poppler_path = r"C:\Program Files\poppler\poppler-25.11.0\Library\bin"
tesseract_path = r"C:\Program Files\Tesseract-OCR"
current_path = os.environ.get('PATH', '')
os.environ['PATH'] = f"{poppler_path};{tesseract_path};{current_path}"

from document_validator import DocumentValidator


class BatchDocumentProcessor:
    """Process multiple PDF and Word documents and export results."""

    def __init__(self, config_file: str = "batch_config.json"):
        """
        Initialize the batch processor.

        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.validator = DocumentValidator(
            log_level=self.config.get('log_level', 'INFO'),
            use_ocr=self.config.get('use_ocr', False)
        )
        self.logger = logging.getLogger(__name__)
        self.results = []

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        default_config = {
            'input_folder': '.',
            'output_folder': 'output',
            'output_formats': ['json', 'csv'],
            'log_level': 'INFO',
            'use_ocr': False,
            'process_subdirectories': False,
            'file_patterns': ['*.pdf', '*.PDF', '*.docx', '*.DOCX']
        }

        if not os.path.exists(config_file):
            print(f"Config file not found: {config_file}")
            print("Using default configuration")
            return default_config

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            return default_config

    def find_documents(self) -> List[str]:
        """Find all documents (PDF, DOCX) in the configured input folder."""
        documents = set()  # Use set to avoid duplicates
        input_folder = Path(self.config['input_folder'])

        if not input_folder.exists():
            self.logger.error(f"Input folder does not exist: {input_folder}")
            return []

        # Search for documents based on file patterns
        if self.config.get('process_subdirectories', False):
            for pattern in self.config['file_patterns']:
                documents.update(input_folder.rglob(pattern))
        else:
            for pattern in self.config['file_patterns']:
                documents.update(input_folder.glob(pattern))

        return sorted([str(f) for f in documents])

    def process_documents(self) -> List[Dict[str, Any]]:
        """Process all documents (PDF, DOCX) in the input folder."""
        document_files = self.find_documents()

        if not document_files:
            self.logger.warning("No documents found to process")
            return []

        self.logger.info(f"Found {len(document_files)} document(s) to process")

        results = []
        for i, document_file in enumerate(document_files, 1):
            self.logger.info(f"Processing {i}/{len(document_files)}: {os.path.basename(document_file)}")

            try:
                result = self.validator.validate_document(document_file)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing {document_file}: {e}")
                results.append({
                    'filename': os.path.basename(document_file),
                    'file_path': document_file,
                    'status': 'error',
                    'error': str(e)
                })

        self.results = results
        return results

    def export_to_json(self, results: List[Dict[str, Any]], output_file: str):
        """Export results to JSON file."""
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Results exported to JSON: {output_file}")

    def export_to_csv(self, results: List[Dict[str, Any]], output_file: str):
        """Export results to CSV file."""
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

        if not results:
            self.logger.warning("No results to export to CSV")
            return

        # Define CSV columns
        columns = [
            'filename',
            'status',
            'agreement_type',
            'agreement_confidence',
            'customer_name',
            'is_signed',
            'signature_confidence',
            'customer_signed',
            'customer_signatory_name',
            'customer_signatory_role',
            'customer_signatory_date',
            'spark_nz_signed',
            'spark_nz_signatory_name',
            'spark_nz_signatory_role',
            'spark_nz_signatory_date',
            'signing_date',
            'has_pricing',
            'pricing_amounts',
            'extracted_dates',
            'text_length',
            'analyzed_at',
            'file_path',
            'error'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for result in results:
                row = {
                    'filename': result.get('filename', ''),
                    'status': result.get('status', ''),
                    'file_path': result.get('file_path', ''),
                    'error': result.get('error', '')
                }

                if result.get('status') == 'success':
                    # Agreement info
                    row['agreement_type'] = result.get('agreement_type', {}).get('type', '')
                    row['agreement_confidence'] = result.get('agreement_type', {}).get('confidence', '')

                    # Customer info
                    row['customer_name'] = result.get('customer_name', '')

                    # Signature info
                    row['is_signed'] = result.get('signature', {}).get('is_signed', False)
                    row['signature_confidence'] = result.get('signature', {}).get('confidence', '')

                    # Signatories
                    customer_sig = result.get('signatories', {}).get('customer', {})
                    row['customer_signed'] = customer_sig.get('signed', False)
                    row['customer_signatory_name'] = customer_sig.get('name', '')
                    row['customer_signatory_role'] = customer_sig.get('role', '')
                    row['customer_signatory_date'] = customer_sig.get('date', '')

                    spark_nz_sig = result.get('signatories', {}).get('spark_nz', {})
                    row['spark_nz_signed'] = spark_nz_sig.get('signed', False)
                    row['spark_nz_signatory_name'] = spark_nz_sig.get('name', '')
                    row['spark_nz_signatory_role'] = spark_nz_sig.get('role', '')
                    row['spark_nz_signatory_date'] = spark_nz_sig.get('date', '')

                    # Dates
                    row['signing_date'] = result.get('signing_date', '')
                    row['extracted_dates'] = ', '.join(result.get('extracted_dates', []))

                    # Pricing
                    pricing = result.get('pricing', {})
                    row['has_pricing'] = pricing.get('has_pricing', False)
                    row['pricing_amounts'] = ', '.join(pricing.get('amounts', []))

                    # Metadata
                    row['text_length'] = result.get('text_length', 0)
                    row['analyzed_at'] = result.get('analyzed_at', '')

                writer.writerow(row)

        self.logger.info(f"Results exported to CSV: {output_file}")

    def run(self):
        """Run the batch processor."""
        print("="*70)
        print("BATCH DOCUMENT PROCESSOR")
        print("="*70)
        print()
        print(f"Input Folder: {self.config['input_folder']}")
        print(f"Output Folder: {self.config['output_folder']}")
        print(f"Output Formats: {', '.join(self.config['output_formats'])}")
        print(f"OCR Enabled: {self.config.get('use_ocr', False)}")
        if not self.config.get('use_ocr', False):
            print("  (Scanned PDFs will fail - enable OCR or use cloud services)")
        print()

        # Process documents
        results = self.process_documents()

        if not results:
            print("No documents processed.")
            return

        # Create output folder
        output_folder = self.config['output_folder']
        os.makedirs(output_folder, exist_ok=True)

        # Generate output filenames with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export to configured formats
        if 'json' in self.config['output_formats']:
            json_file = os.path.join(output_folder, f'document_analysis_{timestamp}.json')
            self.export_to_json(results, json_file)

        if 'csv' in self.config['output_formats']:
            csv_file = os.path.join(output_folder, f'document_analysis_{timestamp}.csv')
            self.export_to_csv(results, csv_file)

        # Print summary
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total documents processed: {len(results)}")
        print(f"Successful: {sum(1 for r in results if r.get('status') == 'success')}")
        print(f"Failed: {sum(1 for r in results if r.get('status') == 'error')}")
        print()

        # Summary by agreement type
        agreement_types = {}
        for r in results:
            if r.get('status') == 'success':
                atype = r.get('agreement_type', {}).get('type', 'Unknown')
                agreement_types[atype] = agreement_types.get(atype, 0) + 1

        if agreement_types:
            print("Agreement Types:")
            for atype, count in sorted(agreement_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {atype}: {count}")
            print()

        # Summary by signature status
        signed = sum(1 for r in results if r.get('status') == 'success' and r.get('signature', {}).get('is_signed'))
        total_success = sum(1 for r in results if r.get('status') == 'success')
        if total_success > 0:
            print(f"Signed documents: {signed}/{total_success}")
            print()

        print("="*70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Batch process PDF documents')
    parser.add_argument('--config', default='batch_config.json', help='Configuration file path')

    args = parser.parse_args()

    processor = BatchDocumentProcessor(args.config)
    processor.run()


if __name__ == '__main__':
    main()
