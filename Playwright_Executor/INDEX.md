# Playwright_Executor - Complete Guide

Welcome to the Playwright Test Case Generator! This folder contains everything you need to create, generate, and run Playwright tests.

## 📁 Quick File Guide

### 🚀 Start Here
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Complete overview of what was implemented

### 📚 Core Documentation  
- **[README.md](README.md)** - Comprehensive API documentation and reference
- **[generate_tests.py](generate_tests.py)** - Command-line tool (run with `--help`)

### 🛠️ Code Files

**Main Generator:**
- **[playwright_test_generator.py](playwright_test_generator.py)** - Core test generation engine

**Configuration & Examples:**
- **[test_config.py](test_config.py)** - Configuration template (CUSTOMIZE THIS!)
- **[sample_generated_test.py](sample_generated_test.py)** - Example of generated test
- **[example_complete_test.py](example_complete_test.py)** - **BEST PRACTICE** - Full example with Page Object Model

### 📁 Folders

**Input:**
- **[TestCases/](TestCases/)** - Put your JSON test case files here
  - `sample_test_input.json` - Example test cases

**Output:**
- **[generated_tests/](generated_tests/)** - Generated Python test files (auto-created)
  - `test_sample_test_input.py` - Example generated test

### 📦 Dependencies
- **[requirements.txt](requirements.txt)** - Python package requirements

## ⚡ Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# List available test case files
python generate_tests.py --list

# Generate tests from your JSON file
python generate_tests.py MyTestCases.json

# Generate all JSON files at once
python generate_tests.py --batch

# Run generated tests
pytest -v generated_tests/

# Run with Playwright browser visible
pytest -v -s generated_tests/

# Run specific test
pytest -v generated_tests/test_sample_test_input.py::test_tc001_user_login_with
```

## 🎯 Typical Workflow

### 1. **Create Test Cases** (JSON)
```bash
# Create file: TestCases/my_app_tests.json
[
  {
    "test_case_id": "TC001",
    "title": "Login test",
    "test_steps": [...],
    "expected_result": "User logged in"
  }
]
```

### 2. **Generate Test Code** (Python)
```bash
python generate_tests.py my_app_tests.json
```

### 3. **Customize Configuration**
Edit `test_config.py`:
- Set BASE_URLS for your app
- Add CSS selectors for your pages
- Configure timeouts

### 4. **Implement Generated Tests**
Edit `generated_tests/test_my_app_tests.py`:
- Replace TODO comments
- Implement actual Playwright code
- Add assertions

### 5. **Run Tests**
```bash
pytest -v generated_tests/
```

## 📖 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **QUICKSTART.md** | Get started in 5 minutes | 5 min |
| **IMPLEMENTATION_SUMMARY.md** | Overview of complete solution | 10 min |
| **README.md** | Full API & reference guide | 20 min |
| **generate_tests.py --help** | CLI options | 2 min |

## 🎓 Learning Path

**Beginner:**
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run: `python generate_tests.py sample_test_input.json`
3. View the generated file in `generated_tests/`

**Intermediate:**
1. Create your own JSON test cases in `TestCases/`
2. Generate tests with your cases
3. Customize `test_config.py` for your app
4. Run tests with pytest

**Advanced:**
1. Look at [example_complete_test.py](example_complete_test.py)
2. Implement Page Object Models
3. Add parametrized tests
4. Integrate with CI/CD

## 🔧 File Structure

```
Playwright_Executor/
├── Index (this file)                    ← YOU ARE HERE
├── QUICKSTART.md                        ← START HERE
├── IMPLEMENTATION_SUMMARY.md            ← READ THIS NEXT
├── README.md                            ← FULL REFERENCE
│
├── Core Files:
├── playwright_test_generator.py         ← Main engine
├── generate_tests.py                    ← CLI tool
│
├── Configuration:
├── test_config.py                       ← CUSTOMIZE THIS
├── requirements.txt                     ← Dependencies
│
├── Examples:
├── sample_generated_test.py             ← Generated example
├── example_complete_test.py             ← BEST PRACTICE example
│
├── Input Folder:
├── TestCases/
│   └── sample_test_input.json          ← Example input
│
└── Output Folder:
    └── generated_tests/
        └── test_sample_test_input.py   ← Generated output
```

## ✨ Key Features

✅ **Automatic Test Generation** - Convert JSON to Playwright tests  
✅ **Best Practices** - Generated tests follow pytest conventions  
✅ **Page Object Model** - Example shows proper test architecture  
✅ **Comprehensive Docs** - Multiple guides for different levels  
✅ **Command-Line Tool** - Easy to use CLI with batch processing  
✅ **Production Ready** - Tests integrate with CI/CD pipelines  
✅ **Customizable** - Configuration template for your app  

## 🚀 Getting Started (2 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate from example
python generate_tests.py sample_test_input.json

# 3. See what was generated
cat generated_tests/test_sample_test_input.py

# 4. View CLI options
python generate_tests.py --help
```

## 📞 Need Help?

**Quick Questions:**
- Check [QUICKSTART.md](QUICKSTART.md)
- Look at [example_complete_test.py](example_complete_test.py)

**Detailed Information:**
- See [README.md](README.md) for complete reference
- Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**CLI Help:**
```bash
python generate_tests.py --help
python generate_tests.py --list
```

## 📋 What This Generates

### Input (JSON)
```json
{
  "test_case_id": "TC001",
  "title": "Login Test",
  "test_steps": [
    {"step_number": 1, "action": "Enter username", "expected": "Username filled"}
  ]
}
```

### Output (Python)
```python
@pytest.mark.high
def test_tc001_login_test(page: Page):
    """Generated test from TC001"""
    page.goto(BASE_URL)
    page.fill("#username", "user@example.com")
    assert page.is_visible("#dashboard")
```

## 🎯 Next Steps

1. **Read:** [QUICKSTART.md](QUICKSTART.md) (5 min)
2. **Try:** Run `python generate_tests.py sample_test_input.json`
3. **Explore:** Check `generated_tests/test_sample_test_input.py`
4. **Customize:** Edit `test_config.py` for your app
5. **Create:** Add your test cases to `TestCases/`
6. **Generate:** Run generator for your cases
7. **Implement:** Fill in the TODO sections
8. **Run:** Execute with pytest

## 📊 Files Summary

| File | Type | Purpose | Status |
|------|------|---------|--------|
| playwright_test_generator.py | Python | Core generator | ✅ Ready |
| generate_tests.py | Python | CLI tool | ✅ Ready |
| test_config.py | Python | Configuration | ✅ Ready to customize |
| sample_generated_test.py | Python | Generated example | ✅ Reference |
| example_complete_test.py | Python | Best practice example | ✅ Reference |
| TestCases/sample_test_input.json | JSON | Example input | ✅ Ready |
| generated_tests/ | Folder | Generated tests | ✅ Auto-created |
| README.md | Doc | Full reference | ✅ Complete |
| QUICKSTART.md | Doc | Quick start | ✅ Complete |
| IMPLEMENTATION_SUMMARY.md | Doc | Implementation details | ✅ Complete |

---

**Ready to start?** → Read [QUICKSTART.md](QUICKSTART.md)

**Need full details?** → Read [README.md](README.md)

**Want to see examples?** → Check [example_complete_test.py](example_complete_test.py)

**Have questions?** → See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
