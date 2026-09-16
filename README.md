# CauseListOCR

**Production-Grade Offline District Court Cause List OCR → Excel Converter**

## Overview

CauseListOCR is a Windows 10/11 desktop application that extracts structured case data from District Court Cause List screenshots with maximum character accuracy, automatic validation, intelligent sorting, and Excel export.

### Key Features

- ✅ **100% Offline Operation** – No internet required after installation
- ✅ **Python 3.14 Native** – Built for the latest Python version
- ✅ **Production OCR** – PaddleOCR + secondary verification
- ✅ **Intelligent Layout Detection** – Dynamic row/column parsing
- ✅ **Multiline Reconstruction** – Smart row joining without data loss
- ✅ **Comprehensive Validation** – Case numbers, dates, duplicates
- ✅ **Natural Sorting** – Numeric case-number ordering (CRLA/2/2026 before CRLA/12/2026)
- ✅ **Manual Review UI** – Approve/edit uncertain records before export
- ✅ **Excel Export** – Formatted, auditable workbook with OCR confidence
- ✅ **Batch Processing** – Handle multiple screenshots and folders
- ✅ **Full Audit Trail** – Raw OCR, normalized, and final data preservation

## System Requirements

### Minimum

- **OS**: Windows 10 (Build 19041+) or Windows 11, 64-bit
- **RAM**: 4 GB (8 GB recommended)
- **Disk**: 2 GB free space for OCR models
- **Python**: 3.14.x (included in standalone EXE)

### For Development

- Python 3.14.x
- Git
- Visual C++ Build Tools (for some NumPy/OpenCV compilations)

## Installation

### Option 1: Standalone EXE (Recommended for End Users)

1. Download `CauseListOCR.exe` from Releases
2. Run the installer
3. No Python installation required

### Option 2: From Source (Developers)

#### Prerequisites

- Python 3.14.x installed
- Git

#### Steps

```bash
# Clone repository
git clone https://github.com/Bodheswaran/CauseListOCR.git
cd CauseListOCR

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements-py314.txt

# Verify Python version
python --version
# Should output: Python 3.14.x

# Run application
python main.py
```

## Usage

### Basic Workflow

1. **Add Images**
   - Click `[Add Images]` to select PNG/JPG screenshots
   - Or `[Add Folder]` for batch processing

2. **Process**
   - Click `[Process]`
   - Application preprocesses, detects layout, and extracts records
   - Progress bar shows real-time status

3. **Review**
   - Records flagged with ⚠️ require verification
   - Click `[Review]` to open manual review screen
   - Inspect source crop, confirm/edit fields

4. **Export**
   - Click `[Export Excel]`
   - Opens `Cause_List_YYYY-MM-DD.xlsx` with:
     - **Cause List** sheet: Final verified data
     - **OCR Audit** sheet: Raw OCR, confidence, review flags

### Supported Image Formats

- PNG
- JPG/JPEG
- BMP
- WEBP
- TIFF

### Extracted Fields

Each case record contains:

| Field | Format | Example |
|-------|--------|----------|
| Case Number | PREFIX/NUMBER/YEAR | CRLA/72/2024 |
| Hearing Date | DD-MM-YYYY | 16-09-2026 |
| Party Name | Full legal name(s) | Dr Rajkumar Radhakrishnaan and another Vs Chief medical officer |
| Advocate | Full advocate name or "-" | Thiru.R. Subramaniyan, ADPP. |

### Sorting Modes

Access via menu: **Sort → Case Prefix + Number + Year**

- **Case Prefix + Number + Year** (default)
  - CRLA/2/2026 → CRLA/12/2026 → CRLA/72/2024 → SC/82/2025

- **Case Number Numeric**
  - Sorts by numeric case ID only

- **Original Screenshot Order**
  - Preserves input file order

## Project Structure

```
CauseListOCR/
├── main.py                    # Application entry point
├── pyproject.toml             # Project configuration
├── requirements-py314.txt     # Python 3.14 dependencies
├── README.md                  # This file
├── build_windows.bat          # Windows EXE builder
├── CauseListOCR.spec          # PyInstaller specification
│
├── app/
│   ├── __init__.py
│   │
│   ├── gui/
│   │   ├── main_window.py     # Primary application UI
│   │   ├── review_window.py   # Manual review interface
│   │   ├── settings_window.py # Configuration dialog
│   │   └── widgets.py         # Custom PySide6 widgets
│   │
│   ├── ocr/
│   │   ├── engine.py          # OCR orchestration
│   │   ├── primary_ocr.py     # PaddleOCR implementation
│   │   ├── secondary_ocr.py   # Optional secondary OCR
│   │   └── confidence.py      # Confidence calculation
│   │
│   ├── preprocessing/
│   │   ├── preprocess.py      # Image enhancement pipeline
│   │   └── image_quality.py   # Quality metrics
│   │
│   ├── layout/
│   │   ├── row_detection.py   # Horizontal row finding
│   │   ├── column_detection.py # Vertical column clustering
│   │   └── table_parser.py    # Table structure analysis
│   │
│   ├── parsing/
│   │   ├── case_number.py     # Case number extraction & validation
│   │   ├── dates.py           # Date parsing & validation
│   │   └── fields.py          # Generic field processing
│   │
│   ├── validation/
│   │   ├── validator.py       # Field-level validation
│   │   ├── duplicate_detector.py # Duplicate case detection
│   │   └── confidence.py      # Confidence scoring
│   │
│   ├── sorting/
│   │   └── case_sorter.py     # Natural case number sorting
│   │
│   ├── export/
│   │   └── excel_exporter.py  # Excel workbook generation
│   │
│   └── utils/
│       ├── config.py          # Configuration management
│       ├── logger.py          # Logging setup
│       ├── paths.py           # Path utilities (Windows-safe)
│       └── models.py          # Data classes
│
├── models/                    # Pre-downloaded OCR models directory
│
├── tests/
│   ├── test_case_sorting.py   # Case number sorting tests
│   ├── test_case_parser.py    # Case number parsing tests
│   ├── test_date_parser.py    # Date validation tests
│   ├── test_duplicates.py     # Duplicate detection tests
│   ├── test_excel_export.py   # Excel output tests
│   └── test_ocr_accuracy.py   # OCR pipeline tests
│
├── samples/                   # Example screenshots
│
├── logs/                      # Application logs
│   └── app.log
│
└── output/                    # Generated Excel files
```

## Development Workflow

### Running Tests

```bash
# All tests
pytest tests/ -v --cov=app

# Specific test file
pytest tests/test_case_sorting.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
```

### Building Windows EXE

```bash
# On Windows command prompt or PowerShell
build_windows.bat

# Output: dist/CauseListOCR.exe
```

### Code Quality

```bash
# Format with Black
black app/ tests/ main.py

# Lint with Ruff
ruff check app/ tests/ main.py

# Type checking
mypy app/ main.py
```

## OCR Model Setup

PaddleOCR models are downloaded automatically on first run and cached locally in `./models/`

- **Installation**: ~500 MB
- **Location**: `models/paddleocr/`
- **Internet**: Required once, then fully offline

### Manual Model Download

```python
from paddleocr import PaddleOCR

# Triggers download
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
print("Models ready.")
```

## Configuration

Edit `app/utils/config.py` to customize:

- OCR preprocessing modes
- Confidence thresholds
- Sorting defaults
- UI appearance
- Logging levels

## Accuracy & Reliability

### Confidence Levels

Each extracted field carries:

- **HIGH** (≥0.85): Auto-accepted
- **MEDIUM** (0.70–0.84): Flagged for review
- **LOW** (<0.70): Requires human verification

### Accuracy Report

After processing, view:

```
Total Records:        125
Accepted:             119 (95.2%)
Needs Review:           4 (3.2%)
Duplicate Candidates:   2 (1.6%)
```

### Data Integrity

**Golden Rule**: The application NEVER fabricates or auto-corrects court data.

If OCR is uncertain → marked for human review → user decides → data exported.

## Troubleshooting

### "No records detected"

- Verify image quality (minimum 150 DPI recommended)
- Check that cause-list table is visible
- Try different preprocessing mode in Settings

### "Module not found: paddleocr"

- Reinstall dependencies: `pip install -r requirements-py314.txt`
- Ensure Python 3.14.x: `python --version`

### "Excel file locked"

- Close any open Excel files named `Cause_List_*.xlsx`
- Try again

### "Incorrect case sorting"

- Verify Sort menu setting
- Check case numbers in OCR Audit sheet for parsing errors
- Review raw OCR in audit sheet if needed

## Performance

| Operation | Time (Typical) |
|-----------|----------------|
| Single image processing | 3–8 seconds |
| 10-image batch | 30–80 seconds |
| Manual review per record | 5–15 seconds |
| Excel export | 1–2 seconds |

*Depends on image quality, system RAM, and CPU speed.*

## Known Limitations

- **Handwritten text**: Not supported (digital print only)
- **Very low quality**: <100 DPI may reduce accuracy
- **Language**: English legal text optimized (Tamil/Hindi support possible with model swap)
- **Non-table layouts**: Assumes structured cause-list table format

## License

MIT License – See LICENSE file for details.

## Support & Contribution

- **Issues**: [GitHub Issues](https://github.com/Bodheswaran/CauseListOCR/issues)
- **Pull Requests**: Contributions welcome
- **Documentation**: See `/docs` directory

## Version History

### v1.0.0 (2026-09-16)

- Initial production release
- Full offline OCR pipeline
- Excel export with audit trail
- Natural case-number sorting
- Windows 10/11 compatibility
- Python 3.14 support

---

**Built for accuracy, validation, and legal data integrity.**
