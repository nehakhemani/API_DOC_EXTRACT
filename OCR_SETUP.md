# OCR Setup Guide for Scanned PDFs

This guide will help you set up OCR (Optical Character Recognition) to process scanned/image-based PDF documents.

## Quick Overview

For scanned PDFs, you need:
1. **Python libraries** (already installed via requirements.txt)
2. **Poppler** (PDF rendering engine)
3. **Tesseract OCR** (text recognition engine)

---

## Windows Setup

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs: `pdf2image`, `pytesseract`, and `Pillow`

### Step 2: Install Poppler (PDF Rendering)

**Option A: Using Pre-built Binaries (Recommended)**

1. Download Poppler for Windows:
   - Go to: https://github.com/oschwartz10612/poppler-windows/releases/
   - Download the latest `Release-XX.XX.X-0.zip`

2. Extract the ZIP file:
   - Extract to `C:\Program Files\poppler`
   - You should have: `C:\Program Files\poppler\Library\bin\`

3. Add Poppler to PATH:
   - Open **System Properties** → **Environment Variables**
   - Under **System Variables**, find **Path**
   - Click **Edit** → **New**
   - Add: `C:\Program Files\poppler\Library\bin`
   - Click **OK** to save

4. Verify installation:
   ```bash
   pdftoppm -v
   ```
   Should show version information

**Option B: Using Conda (if you use Anaconda)**

```bash
conda install -c conda-forge poppler
```

### Step 3: Install Tesseract OCR

1. Download Tesseract installer:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download `tesseract-ocr-w64-setup-X.X.X.XXXXX.exe`

2. Run the installer:
   - Use default installation path: `C:\Program Files\Tesseract-OCR`
   - **Important**: Check "Add to PATH" during installation
   - Select language packs (at minimum: English)

3. Verify installation:
   ```bash
   tesseract --version
   ```
   Should show: `tesseract v5.x.x`

4. If NOT in PATH, add manually:
   - Add to PATH: `C:\Program Files\Tesseract-OCR`
   - Restart your terminal/command prompt

### Step 4: Test OCR

```bash
python document_validator.py "your-scanned-document.pdf"
```

You should see:
```
INFO - OCR support available for scanned PDFs
INFO - No text found with standard methods, trying OCR...
INFO - Performing OCR on scanned PDF (processing up to 5 pages)...
INFO - OCR processing page 1/5...
```

---

## Linux Setup

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt

# Verify
pdftoppm -v
tesseract --version
```

### CentOS/RHEL/Fedora

```bash
# Install system dependencies
sudo yum install -y poppler-utils tesseract

# Install Python dependencies
pip install -r requirements.txt
```

---

## macOS Setup

### Using Homebrew

```bash
# Install system dependencies
brew install poppler tesseract

# Install Python dependencies
pip install -r requirements.txt

# Verify
pdftoppm -v
tesseract --version
```

---

## Troubleshooting

### Error: "Unable to get page count. Is poppler installed and in PATH?"

**Solution:**
- Poppler is not installed or not in PATH
- On Windows: Make sure `C:\Program Files\poppler\Library\bin` is in your PATH
- Restart your terminal after adding to PATH
- Verify with: `pdftoppm -v`

### Error: "tesseract is not installed or it's not in your PATH"

**Solution:**
- Tesseract is not installed or not in PATH
- On Windows: Make sure `C:\Program Files\Tesseract-OCR` is in your PATH
- Restart your terminal after adding to PATH
- Verify with: `tesseract --version`

### Error: "OCR not available. Install pdf2image and pytesseract"

**Solution:**
```bash
pip install pdf2image pytesseract Pillow
```

### OCR is very slow

**Solution:**
- OCR processes up to 5 pages by default (scanned PDFs can be large)
- For full document processing, modify the code or use a specific page range
- Consider processing only signature pages if you know which pages they're on

### OCR produces poor quality text

**Solutions:**
- Ensure the PDF has good scan quality (minimum 200 DPI)
- Install additional Tesseract language packs if needed
- Use `--log-level DEBUG` to see detailed OCR output

---

## Advanced Configuration

### Process More Pages

By default, OCR processes up to 5 pages. To change this:

```python
# In document_validator.py, modify the extract_text_ocr method
def extract_text_ocr(self, pdf_path: str, max_pages: int = 10):  # Changed from 5 to 10
```

### Specify Tesseract Path (if not in PATH)

Add to your code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Install Additional Languages

Download language packs from:
https://github.com/tesseract-ocr/tessdata

Place `.traineddata` files in:
- Windows: `C:\Program Files\Tesseract-OCR\tessdata`
- Linux: `/usr/share/tesseract-ocr/5/tessdata`
- macOS: `/opt/homebrew/share/tessdata`

---

## Verifying Your Setup

Run this test:

```bash
python -c "
from pdf2image import convert_from_path
import pytesseract
print('✓ pdf2image imported successfully')
print('✓ pytesseract imported successfully')
print(f'Tesseract version: {pytesseract.get_tesseract_version()}')
"
```

Expected output:
```
✓ pdf2image imported successfully
✓ pytesseract imported successfully
Tesseract version: 5.x.x
```

---

## Performance Tips

1. **Limit pages**: Process only the pages you need (signatures are usually at the end)
2. **Reduce DPI**: Default is 200 DPI, can lower to 150 for faster processing
3. **Pre-process**: If you have many documents, consider batch processing overnight
4. **Cache results**: Save OCR results to avoid re-processing same documents

---

## Need Help?

If you encounter issues:

1. Check that both Poppler and Tesseract are in your PATH
2. Restart your terminal/IDE after installing
3. Try the verification commands above
4. Check the error messages in the validator output
5. Use `--log-level DEBUG` for detailed diagnostics

---

## Resources

- **Poppler**: https://poppler.freedesktop.org/
- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **pdf2image**: https://github.com/Belval/pdf2image
- **pytesseract**: https://github.com/madmaze/pytesseract
