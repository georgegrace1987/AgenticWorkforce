# Playwright Test Executor - Web Dashboard

## Overview

The Playwright Test Executor now includes a web-based dashboard that provides real-time analytics and insights into your test cases. The dashboard displays key metrics about test case readiness for Playwright automation.

## Features

### 📊 Dashboard Metrics

The dashboard displays **5 key statistics**:

1. **Excel Files** - Total number of Excel files in the TestCases folder
2. **Total Test Cases** - Sum of all test cases across all files
3. **Valid for Playwright** - Test cases that have the required fields for Playwright automation
4. **Cleared for Execution** - Test cases marked with `automation_candidate = Yes`
5. **Generated Tests** - Number of test files already generated

### 📋 Test Case Files Table

A detailed table showing:
- **File Name** - Name of the Excel file
- **Total Cases** - Count of test cases in file
- **Valid** - Count of test cases with required fields
- **Cleared** - Count of test cases ready for automation
- **Status** - Visual status badge (Ready, Partial, Pending)

### 🔄 Auto-Refresh

The dashboard automatically refreshes statistics every 30 seconds.

## Starting the Dashboard

### From AgenticWorkforce Launcher

1. Open the main launcher: `http://127.0.0.1:8000`
2. Click "Launch workspace" on the **Playwright Test Executor** card
3. Dashboard will open at: `http://127.0.0.1:8002`

### From Command Line

```bash
cd Playwright_Executor
python app.py
```

Dashboard will be available at: `http://127.0.0.1:8002`

## Test Case Excel Format

Your Excel files should have the following columns:

### Required Columns (for valid test cases):
- `test_case_id` - Unique identifier (e.g., TC001)
- `title` - Test case name/description
- `test_steps` - Steps to execute (e.g., "1. Go to login; 2. Enter password")
- `expected_result` - Expected outcome

### Optional Columns:
- `description` - Detailed description
- `preconditions` - Setup requirements
- `postconditions` - Cleanup actions
- `automation_candidate` - **"Yes"** to mark as cleared for Playwright
- `test_type` - Type (Functional, Regression, Smoke, UI, etc.)
- `priority` - Priority level (High, Medium, Low)

### Example:

```
| test_case_id | title                       | test_steps                           | expected_result           | automation_candidate |
|--------------|-----------------------------|------------------------------------|------------------------|----------------------|
| TC001        | Login with valid creds     | 1. Go to login; 2. Enter email...  | User logged in         | Yes                  |
| TC002        | Invalid login              | 1. Go to login; 2. Wrong password  | Error message shown    | Yes                  |
| TC003        | Check field layout         | 1. Go to login; 2. Verify fields   | All fields visible     | No                   |
```

## Understanding the Metrics

### ✅ Valid Test Cases
A test case is **valid for Playwright** if it contains:
- At least one identifier field (test_case_id, id, title, or name)
- Test steps field (test_steps or steps)
- Expected result field (expected_result or expected)

### ✅ Cleared Test Cases
A test case is **cleared for execution** if it is **valid** AND has:
- `automation_candidate` column set to: `Yes`, `True`, `1`, or `Y`

### 📊 Test Case Flow

```
All Test Cases
    ↓
    ├─→ Invalid (missing required fields)
    ├─→ Valid (has all required fields)
        ├─→ Not Cleared (automation_candidate ≠ Yes)
        └─→ Cleared (automation_candidate = Yes) ✓ Ready for Playwright
```

## Status Badges

### 🟢 Ready (Cleared)
- Test case is **cleared for automation** (`automation_candidate = Yes`)
- Shows count of cleared cases
- These are ready to be used in Playwright tests

### 🟡 Partial (Valid but not cleared)
- Test case has **all required fields** but not marked for automation
- Can be converted to Playwright tests after review
- Review and update `automation_candidate` field to enable

### ⚫ Pending (Not valid)
- Test case is **missing required fields**
- Cannot be converted to Playwright tests yet
- Complete the missing information

## API Endpoints

### Get Statistics (JSON)
```
GET /api/stats
```

Returns all dashboard statistics in JSON format.

### Get Files List (JSON)
```
GET /api/files
```

Returns detailed information about all test case files.

## Adding Test Cases

### Method 1: Upload Excel File
1. Create an Excel file with the required columns
2. Save it in the `TestCases/` folder
3. Refresh the dashboard
4. Statistics will update automatically

### Method 2: Use Template
1. Run: `python create_sample_excel.py`
2. This creates `sample_test_cases.xlsx` with example data
3. Modify the file with your test cases
4. Dashboard will reflect the changes

## Working with Dashboard Data

### Next Steps After Reviewing Dashboard

1. **Identify cleared test cases** - See which cases are ready for automation
2. **Generate Playwright code** - Use the CLI tool:
   ```bash
   python generate_tests.py your_file.xlsx
   ```
3. **Review generated tests** - Check `generated_tests/` folder
4. **Implement and run tests** - Execute with pytest:
   ```bash
   pytest -v generated_tests/
   ```

## Troubleshooting

### Dashboard shows 0 files
- Ensure Excel files are in the `TestCases/` folder
- Check file names don't have special characters
- Supported formats: `.xlsx`, `.xls`, `.xlsm`

### Statistics not updating
- Refresh browser page (F5)
- Check browser console for errors
- Ensure app is still running

### Can't start the app
- Verify dependencies are installed: `pip install -r requirements.txt`
- Check if port 8002 is available
- Try running from the Playwright_Executor directory

## Dashboard Architecture

### Frontend
- **Framework**: HTML5 + CSS3 (no JavaScript framework)
- **Styling**: Custom CSS with responsive design
- **Auto-refresh**: JavaScript fetch API (every 30 seconds)

### Backend
- **Framework**: Flask
- **Data Processing**: Pandas + openpyxl
- **Language**: Python

### Data Flow
```
Excel Files (TestCases/)
    ↓ (Flask reads)
    ↓ (Pandas processes)
    ↓
Statistics Calculated
    ↓
JSON API (/api/stats)
    ↓
Dashboard Display
```

## Tips & Best Practices

✅ **Keep test files organized** - Use clear file names (e.g., `login_tests.xlsx`, `checkout_tests.xlsx`)

✅ **Use consistent field values** - For automation_candidate, use "Yes" or "No" consistently

✅ **Review statistics regularly** - Check the dashboard before each test run

✅ **Document test cases** - Add descriptions and clear test steps

✅ **Use priorities** - Mark critical tests as High priority

✅ **Track status** - Monitor how many tests are cleared for automation

## Keyboard Shortcuts

- **Refresh Dashboard**: `F5` (browser)
- **Auto-refresh**: Happens every 30 seconds automatically

## Support

For issues with:
- **Test case format** → Check "Test Case Excel Format" section above
- **Dashboard statistics** → See "Understanding the Metrics" section
- **File location** → Ensure files are in `TestCases/` folder
- **App startup** → Check "Troubleshooting" section

---

**Dashboard URL**: `http://127.0.0.1:8002`  
**Auto-refresh**: Every 30 seconds  
**Last Modified**: 2026-09-05
