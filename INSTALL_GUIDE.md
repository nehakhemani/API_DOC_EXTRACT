# Quick Installation Guide for OCR Tools

Follow these steps to install Poppler and Tesseract on Windows.

---

## Part 1: Install Poppler

### Download Poppler

1. Go to: **https://github.com/oschwartz10612/poppler-windows/releases/**
2. Download the latest `Release-XX.XX.X-0.zip` (about 20-30 MB)
3. Save to your Downloads folder

### Install Poppler

1. **Extract the ZIP:**
   - Right-click the downloaded ZIP file
   - Select "Extract All..."
   - Extract to a temporary location (e.g., Downloads)

2. **Copy to Program Files:**
   - Open File Explorer
   - Navigate to `C:\Program Files\`
   - Create a new folder called `poppler`
   - Copy the contents from the extracted folder into `C:\Program Files\poppler\`
   - You should have: `C:\Program Files\poppler\Library\bin\pdftoppm.exe`

### Add Poppler to PATH

**Option 1: Using GUI (Recommended)**

1. Press `Windows Key` and search for "Environment Variables"
2. Click "Edit the system environment variables"
3. Click "Environment Variables..." button
4. Under "System variables" (bottom section), find "Path"
5. Click "Edit..."
6. Click "New"
7. Add: `C:\Program Files\poppler\Library\bin`
8. Click "OK" on all windows

**Option 2: Using Command Line**

1. Open Command Prompt **as Administrator**
2. Run:
   ```cmd
   setx /M PATH "%PATH%;C:\Program Files\poppler\Library\bin"
   ```

### Verify Poppler Installation

1. **Close all terminal/command prompt windows**
2. Open a **new** Command Prompt
3. Run:
   ```cmd
   pdftoppm -v
   ```
4. You should see version information like: `pdftoppm version 24.08.0`

✅ If you see version info, Poppler is installed correctly!

---

## Part 2: Install Tesseract OCR

### Download Tesseract

1. Go to: **https://github.com/UB-Mannheim/tesseract/wiki**
2. Look for the download section
3. Click the link for the latest version (e.g., `tesseract-ocr-w64-setup-5.4.0.20240606.exe`)
4. Download the installer (about 50-60 MB)

### Install Tesseract

1. **Run the Installer:**
   - Double-click the downloaded `.exe` file
   - Click "Yes" if asked for admin permission

2. **Installation Options:**
   - Select installation directory (default: `C:\Program Files\Tesseract-OCR`)
   - **Important:** Check the box "Add to PATH" during installation
   - Select language packs:
     - ✅ English (required)
     - Select any other languages you need
   - Click "Install"

3. **Complete Installation:**
   - Wait for installation to complete
   - Click "Finish"

### Verify Tesseract Installation

1. **Close all terminal/command prompt windows**
2. Open a **new** Command Prompt
3. Run:
   ```cmd
   tesseract --version
   ```
4. You should see version information like: `tesseract v5.4.0`

✅ If you see version info, Tesseract is installed correctly!

### If Tesseract is NOT in PATH

If the command doesn't work, manually add to PATH:

1. Press `Windows Key` and search for "Environment Variables"
2. Click "Edit the system environment variables"
3. Click "Environment Variables..." button
4. Under "System variables" (bottom section), find "Path"
5. Click "Edit..."
6. Click "New"
7. Add: `C:\Program Files\Tesseract-OCR`
8. Click "OK" on all windows

---

## Part 3: Test Your Setup

After installing both Poppler and Tesseract:

1. **Close ALL terminal/command prompt/PowerShell windows**
2. Open a **new** Command Prompt or PowerShell
3. Navigate to your project:
   ```cmd
   cd C:\Users\NEHA\Documents\PDF_CCL
   ```

4. **Verify both tools:**
   ```cmd
   pdftoppm -v
   tesseract --version
   ```

5. **Test the validator:**
   ```cmd
   python document_validator.py "25490Q.1 Mobile Signed.pdf"
   ```

You should see:
```
INFO - OCR support available for scanned PDFs
INFO - Performing OCR on scanned PDF (processing up to 5 pages)...
INFO - OCR processing page 1/5...
INFO - OCR processing page 2/5...
...
```

---

## Troubleshooting

### "pdftoppm is not recognized" or "tesseract is not recognized"

**Solution:**
- The tool is not in your PATH
- Make sure you added the correct directory to PATH
- **Restart your terminal** after adding to PATH (very important!)
- Try opening a completely new terminal window

### "Permission denied" when copying to Program Files

**Solution:**
- Right-click File Explorer → Run as Administrator
- Or copy to a user directory like `C:\Users\NEHA\poppler` instead
- Update PATH to point to your custom location

### OCR is very slow

**Normal behavior:**
- OCR processes 5 pages by default (can take 30-60 seconds per page)
- This is normal for scanned documents
- Be patient during first run

### Still having issues?

1. Check that both tools are in PATH:
   ```cmd
   echo %PATH%
   ```
   Look for the Poppler and Tesseract directories

2. Restart your computer (sometimes required for PATH changes)

3. Check OCR_SETUP.md for more detailed troubleshooting

---

## Quick Reference

**Poppler Download:**
https://github.com/oschwartz10612/poppler-windows/releases/

**Tesseract Download:**
https://github.com/UB-Mannheim/tesseract/wiki

**Poppler PATH:**
`C:\Program Files\poppler\Library\bin`

**Tesseract PATH:**
`C:\Program Files\Tesseract-OCR`

---

## After Installation

Once both are installed, you can process scanned PDFs:

```cmd
# Single document
python document_validator.py "scanned-document.pdf"

# Entire directory
python document_validator.py scanned_pdfs/

# Save results to JSON
python document_validator.py "scanned-document.pdf" --output results.json
```

Good luck! 🚀
