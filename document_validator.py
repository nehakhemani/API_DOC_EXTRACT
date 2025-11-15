"""
PDF Document Validator and Information Extractor

Analyzes PDF documents to extract key information such as:
- Signature status
- Signing date
- Customer/client name
- Agreement type
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class DocumentValidator:
    """Validates and extracts information from PDF documents."""

    # Common signature indicators
    SIGNATURE_KEYWORDS = [
        r'signature',
        r'signed\s+by',
        r'electronically\s+signed',
        r'digitally\s+signed',
        r'/s/',
        r'authorized\s+signatory',
        r'executed\s+by',
        r'signed\s+on',
        r'date\s+signed',
        r'signature\s+date'
    ]

    # Date patterns (various formats)
    DATE_PATTERNS = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',     # YYYY/MM/DD
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b',  # Month DD, YYYY
        r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\b',  # DD Month YYYY
    ]

    # Agreement type patterns
    AGREEMENT_TYPES = {
        'service_agreement': [r'service\s+agreement', r'service\s+contract'],
        'business_agreement': [r'business\s+agreement', r'general\s+business\s+agreement'],
        'license_agreement': [r'license\s+agreement', r'licensing\s+agreement'],
        'nda': [r'non[-\s]?disclosure\s+agreement', r'confidentiality\s+agreement', r'NDA'],
        'sales_agreement': [r'sales\s+agreement', r'purchase\s+agreement'],
        'employment_agreement': [r'employment\s+agreement', r'employment\s+contract'],
        'partnership_agreement': [r'partnership\s+agreement'],
        'lease_agreement': [r'lease\s+agreement', r'rental\s+agreement'],
        'master_agreement': [r'master\s+agreement', r'master\s+service\s+agreement', r'MSA'],
    }

    def __init__(self, log_level: str = "INFO"):
        """Initialize the document validator."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level))

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

        self._check_dependencies()

    def _check_dependencies(self):
        """Check which PDF libraries are available."""
        if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            self.logger.warning("No PDF libraries available. Install PyPDF2 or pdfplumber for full functionality.")
        elif PDFPLUMBER_AVAILABLE:
            self.logger.info("Using pdfplumber for PDF extraction")
        elif PYPDF2_AVAILABLE:
            self.logger.info("Using PyPDF2 for PDF extraction")

    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text from PDF using PyPDF2."""
        if not PYPDF2_AVAILABLE:
            return ""

        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction failed: {e}")

        return text

    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        if not PDFPLUMBER_AVAILABLE:
            return ""

        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            self.logger.error(f"pdfplumber extraction failed: {e}")

        return text

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF using available libraries.
        Tries pdfplumber first, falls back to PyPDF2.
        """
        if not os.path.exists(pdf_path):
            self.logger.error(f"File not found: {pdf_path}")
            return ""

        # Try pdfplumber first (generally better)
        if PDFPLUMBER_AVAILABLE:
            text = self.extract_text_pdfplumber(pdf_path)
            if text.strip():
                return text

        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            text = self.extract_text_pypdf2(pdf_path)
            if text.strip():
                return text

        self.logger.warning(f"Could not extract text from {pdf_path}")
        return ""

    def detect_signature(self, text: str) -> Dict[str, Any]:
        """
        Detect if document appears to be signed based on keywords and patterns.

        Returns:
            dict with 'is_signed' (bool), 'confidence' (str), and 'indicators' (list)
        """
        text_lower = text.lower()
        found_indicators = []

        for pattern in self.SIGNATURE_KEYWORDS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                found_indicators.append(match.group())

        # Determine confidence level
        indicator_count = len(found_indicators)
        if indicator_count >= 3:
            confidence = "high"
            is_signed = True
        elif indicator_count >= 1:
            confidence = "medium"
            is_signed = True
        else:
            confidence = "low"
            is_signed = False

        return {
            'is_signed': is_signed,
            'confidence': confidence,
            'indicator_count': indicator_count,
            'indicators': list(set(found_indicators))[:5]  # Unique, max 5
        }

    def extract_dates(self, text: str) -> List[str]:
        """Extract potential dates from document text."""
        dates = []

        for pattern in self.DATE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append(match.group(1))

        # Remove duplicates while preserving order
        seen = set()
        unique_dates = []
        for date in dates:
            if date not in seen:
                seen.add(date)
                unique_dates.append(date)

        return unique_dates

    def extract_signing_date(self, text: str) -> Optional[str]:
        """
        Extract the most likely signing date from document.
        Looks for dates near signature-related keywords.
        """
        lines = text.split('\n')
        signing_date = None

        # Look for dates near signature keywords
        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if line contains signature-related keywords
            for keyword_pattern in ['date.*signed', 'signed.*date', 'signature.*date', 'executed.*date']:
                if re.search(keyword_pattern, line_lower):
                    # Look for date in this line and next few lines
                    context = '\n'.join(lines[i:min(i+3, len(lines))])
                    dates = self.extract_dates(context)
                    if dates:
                        signing_date = dates[0]
                        break

            if signing_date:
                break

        # If no signing date found, return the last date in document (common pattern)
        if not signing_date:
            all_dates = self.extract_dates(text)
            if all_dates:
                signing_date = all_dates[-1]

        return signing_date

    def extract_customer_name(self, text: str, filename: str = "") -> Optional[str]:
        """
        Extract customer/client name from document.
        Uses filename parsing and text patterns.
        """
        # Try to extract from filename first (common pattern: ID_CUSTOMERNAME_DocumentType.pdf)
        if filename:
            parts = filename.replace('.pdf', '').replace('.PDF', '').split('_')
            if len(parts) >= 2:
                # Second part is usually customer name
                customer_name = parts[1].strip()
                if customer_name and len(customer_name) > 2:
                    return customer_name.replace('_', ' ').title()

        # Try to find in document text
        patterns = [
            r'(?:client|customer|company)\s*(?:name)?:\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|LLC|Inc|Corp|Limited|Co)?)',
            r'(?:between|with)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|LLC|Inc|Corp|Limited|Co)?)\s+(?:and|&)',
            r'This\s+agreement.*?(?:between|with)\s+([A-Z][A-Za-z\s&.,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up and validate
                if len(name) > 3 and len(name) < 100:
                    return name

        return None

    def detect_agreement_type(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Detect the type of agreement from document text and filename.

        Returns:
            dict with 'type', 'confidence', and 'matched_pattern'
        """
        text_lower = text.lower()
        combined_text = f"{filename} {text_lower}"

        matches = []

        for agreement_type, patterns in self.AGREEMENT_TYPES.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    # Count occurrences for confidence
                    count = len(re.findall(pattern, combined_text, re.IGNORECASE))
                    matches.append({
                        'type': agreement_type.replace('_', ' ').title(),
                        'pattern': pattern,
                        'count': count
                    })

        if not matches:
            return {'type': 'Unknown', 'confidence': 'low', 'matched_pattern': None}

        # Sort by count and pick the best match
        best_match = sorted(matches, key=lambda x: x['count'], reverse=True)[0]

        confidence = 'high' if best_match['count'] >= 2 else 'medium'

        return {
            'type': best_match['type'],
            'confidence': confidence,
            'matched_pattern': best_match['pattern']
        }

    def validate_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Perform complete validation and information extraction on a PDF document.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing all extracted information
        """
        self.logger.info(f"Validating document: {pdf_path}")

        # Get filename
        filename = os.path.basename(pdf_path)

        # Extract text
        text = self.extract_text(pdf_path)

        if not text.strip():
            return {
                'filename': filename,
                'status': 'error',
                'error': 'Could not extract text from PDF',
                'file_path': pdf_path
            }

        # Perform all extractions
        signature_info = self.detect_signature(text)
        signing_date = self.extract_signing_date(text)
        customer_name = self.extract_customer_name(text, filename)
        agreement_info = self.detect_agreement_type(text, filename)
        all_dates = self.extract_dates(text)

        # Compile results
        results = {
            'filename': filename,
            'file_path': pdf_path,
            'status': 'success',
            'signature': {
                'is_signed': signature_info['is_signed'],
                'confidence': signature_info['confidence'],
                'indicators_found': signature_info['indicator_count'],
                'signature_indicators': signature_info['indicators']
            },
            'signing_date': signing_date,
            'customer_name': customer_name,
            'agreement_type': {
                'type': agreement_info['type'],
                'confidence': agreement_info['confidence']
            },
            'extracted_dates': all_dates[:10],  # Limit to first 10 dates
            'text_length': len(text),
            'analyzed_at': datetime.now().isoformat()
        }

        self.logger.info(f"Validation complete: {results['agreement_type']['type']} - Signed: {results['signature']['is_signed']}")

        return results

    def validate_directory(self, directory: str, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Validate all PDF files in a directory.

        Args:
            directory: Path to directory containing PDFs
            output_file: Optional JSON file path to save results

        Returns:
            List of validation results for each PDF
        """
        results = []
        pdf_files = list(Path(directory).glob('*.pdf')) + list(Path(directory).glob('*.PDF'))

        self.logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        for pdf_path in pdf_files:
            result = self.validate_document(str(pdf_path))
            results.append(result)

        # Save to JSON if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Results saved to {output_file}")

        return results

    def print_summary(self, result: Dict[str, Any]):
        """Print a formatted summary of validation results."""
        print("\n" + "="*60)
        print(f"Document: {result['filename']}")
        print("="*60)

        if result['status'] == 'error':
            print(f"Error: {result['error']}")
            return

        print(f"\nAgreement Type: {result['agreement_type']['type']} ({result['agreement_type']['confidence']} confidence)")
        print(f"Customer Name: {result['customer_name'] or 'Not detected'}")
        print(f"Signed: {'Yes' if result['signature']['is_signed'] else 'No'} ({result['signature']['confidence']} confidence)")
        print(f"Signing Date: {result['signing_date'] or 'Not detected'}")

        if result['signature']['signature_indicators']:
            print(f"\nSignature Indicators Found: {', '.join(result['signature']['signature_indicators'][:3])}")

        if result['extracted_dates']:
            print(f"\nDates Found: {', '.join(result['extracted_dates'][:5])}")

        print("\n" + "="*60)


def main():
    """Command-line interface for document validation."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate and extract information from PDF documents')
    parser.add_argument('path', help='PDF file or directory path')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')

    args = parser.parse_args()

    validator = DocumentValidator(log_level=args.log_level)

    if os.path.isfile(args.path):
        # Single file
        result = validator.validate_document(args.path)
        validator.print_summary(result)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {args.output}")

    elif os.path.isdir(args.path):
        # Directory
        results = validator.validate_directory(args.path, args.output)

        print(f"\n{'='*60}")
        print(f"Processed {len(results)} documents")
        print(f"{'='*60}")

        # Summary statistics
        signed_count = sum(1 for r in results if r.get('signature', {}).get('is_signed'))
        print(f"\nSigned documents: {signed_count}/{len(results)}")

        # Agreement types
        types = {}
        for r in results:
            atype = r.get('agreement_type', {}).get('type', 'Unknown')
            types[atype] = types.get(atype, 0) + 1

        print("\nAgreement Types:")
        for atype, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {atype}: {count}")

    else:
        print(f"Error: {args.path} is not a valid file or directory")


if __name__ == '__main__':
    main()
