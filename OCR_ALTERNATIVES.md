# OCR Alternatives for Corporate Environments

This document provides alternatives to local OCR installation (Tesseract/Poppler), which may not be allowed in corporate environments.

## Overview

The document validator can work in **two modes**:

1. **Without OCR** (default): Standard PDF and DOCX text extraction only
2. **With OCR**: Handles scanned/image-based PDFs (requires additional installation)

## Configuration

Edit `batch_config.json`:

```json
{
  "use_ocr": false    // Set to true only if OCR libraries are installed
}
```

## When OCR is Disabled (Default)

### What Works
✅ PDF files with extractable text
✅ DOCX files (Word documents)
✅ Hybrid PDFs (some text, some images)

### What Fails
❌ Fully scanned PDFs (image-only)
❌ PDFs created from scanned documents
❌ Image-based PDFs

**Error Message:**
```
ERROR - Document appears to be scanned/image-based (only 21 characters extracted)
ERROR - → This document requires OCR processing
ERROR - → Enable OCR in batch_config.json: "use_ocr": true
ERROR - → Alternative: Use cloud-based OCR services
```

## Cloud-Based OCR Alternatives

### 1. Azure AI Document Intelligence (Recommended for Enterprise)

**Best for:** Corporate environments, high accuracy, compliance

**Features:**
- Pre-built models for invoices, receipts, business cards
- Custom model training
- Table/form recognition
- SOC 2, ISO 27001 certified

**Setup:**
```python
pip install azure-ai-formrecognizer
```

**Basic Usage:**
```python
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

endpoint = "YOUR_ENDPOINT"
key = "YOUR_KEY"

client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

with open("document.pdf", "rb") as f:
    poller = client.begin_analyze_document("prebuilt-document", f)
    result = poller.result()

# Extract text
text = result.content
```

**Pricing:**
- Free tier: 500 pages/month
- Paid: $1.50 per 1000 pages

**Documentation:**
https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/

---

### 2. AWS Textract

**Best for:** AWS-based infrastructure, integration with AWS services

**Features:**
- Text and table extraction
- Form data extraction
- Identity document analysis
- HIPAA, PCI DSS compliant

**Setup:**
```python
pip install boto3
```

**Basic Usage:**
```python
import boto3

textract = boto3.client('textract')

with open('document.pdf', 'rb') as f:
    response = textract.detect_document_text(
        Document={'Bytes': f.read()}
    )

# Extract text
text = ""
for item in response['Blocks']:
    if item['BlockType'] == 'LINE':
        text += item['Text'] + '\n'
```

**Pricing:**
- First 1M pages/month: $1.50 per 1000 pages
- Over 1M pages: $0.60 per 1000 pages

**Documentation:**
https://aws.amazon.com/textract/

---

### 3. Google Cloud Vision API

**Best for:** Google Cloud Platform users, multi-language support

**Features:**
- OCR in 200+ languages
- Handwriting detection
- PDF/TIFF support
- ISO 27001, SOC 2/3 certified

**Setup:**
```python
pip install google-cloud-vision
```

**Basic Usage:**
```python
from google.cloud import vision

client = vision.ImageAnnotatorClient()

with open('document.pdf', 'rb') as f:
    content = f.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)

# Extract text
text = response.full_text_annotation.text
```

**Pricing:**
- First 1000 units/month: Free
- Next units: $1.50 per 1000 units

**Documentation:**
https://cloud.google.com/vision/docs/ocr

---

### 4. Adobe PDF Services API

**Best for:** Existing Adobe infrastructure, high-quality PDFs

**Features:**
- PDF text extraction
- PDF manipulation (split, merge, compress)
- Conversion to/from Office formats
- Enterprise-grade security

**Setup:**
```python
pip install pdfservices-sdk
```

**Pricing:**
- Free tier: 500 operations/month
- Paid plans available

**Documentation:**
https://developer.adobe.com/document-services/

---

## Comparison Matrix

| Service | Free Tier | Enterprise Ready | Best For | Setup Difficulty |
|---------|-----------|------------------|----------|------------------|
| Azure AI | 500 pages/mo | ✅ Yes | Corporate/Compliance | Easy |
| AWS Textract | Usage-based | ✅ Yes | AWS Ecosystem | Easy |
| Google Vision | 1000 units/mo | ✅ Yes | Multi-language | Easy |
| Adobe PDF | 500 ops/mo | ✅ Yes | PDF Processing | Medium |

---

## Implementation Recommendations

### For Corporate/Work Environments:

1. **Check existing cloud subscriptions**
   - If using Azure: Use Azure AI Document Intelligence
   - If using AWS: Use AWS Textract
   - If using GCP: Use Google Cloud Vision

2. **Create a separate OCR service module**
   ```
   project/
   ├── document_validator.py  (no OCR dependencies)
   ├── ocr_service.py          (cloud OCR integration)
   └── batch_processor.py
   ```

3. **Use configuration for cloud service selection**
   ```json
   {
     "use_ocr": false,
     "cloud_ocr_service": "azure",
     "cloud_ocr_config": {
       "endpoint": "YOUR_ENDPOINT",
       "key": "YOUR_KEY"
     }
   }
   ```

### For Development/Testing:

- Use the built-in OCR with Tesseract/Poppler (see `OCR_SETUP.md`)
- Or use free tiers of cloud services

---

## Security Considerations

When using cloud OCR services:

1. **Data Privacy**
   - Documents are sent to cloud providers
   - Check data residency requirements
   - Review service provider's data handling policies

2. **Compliance**
   - Ensure service is compliant with your requirements (GDPR, HIPAA, etc.)
   - Use private endpoints if available
   - Enable encryption in transit and at rest

3. **API Key Management**
   - Never commit API keys to version control
   - Use environment variables or key vaults
   - Rotate keys regularly

---

## Cost Optimization

1. **Batch processing**: Group documents to reduce API calls
2. **Caching**: Store OCR results to avoid re-processing
3. **Pre-filtering**: Skip documents that already have extractable text
4. **Compression**: Reduce document size before sending to cloud

---

## Next Steps

1. Disable OCR in `batch_config.json` (default)
2. Test with your documents
3. For scanned PDFs: Choose a cloud OCR service based on your environment
4. Implement cloud OCR integration as needed

---

## Support

For questions about:
- **Built-in OCR setup**: See `OCR_SETUP.md`
- **Cloud service setup**: Refer to service provider documentation
- **Document validation**: See `README.md`
