"""
Playwright Test Executor - Web UI

Flask application for displaying test statistics and managing Playwright test generation.
"""

import os
import json
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import openpyxl
import pandas as pd
from datetime import datetime
import traceback

app = Flask(__name__)

# Configuration
BASE_DIR = Path(__file__).resolve().parent
TEST_CASES_DIR = BASE_DIR / "TestCases"
UPLOADS_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated_tests"

# Ensure directories exist
TEST_CASES_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)


def get_excel_files():
    """Get all Excel files in TestCases directory."""
    excel_extensions = ('.xlsx', '.xls', '.xlsm')
    files = []
    
    if TEST_CASES_DIR.exists():
        for file in TEST_CASES_DIR.glob('*'):
            if file.suffix.lower() in excel_extensions:
                files.append(file)
    
    return sorted(files)


def count_test_cases_in_file(filepath):
    """Count test cases in an Excel file."""
    try:
        if filepath.suffix.lower() == '.xlsx':
            df = pd.read_excel(filepath, sheet_name=0)
        else:
            df = pd.read_excel(filepath)
        
        return len(df)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0


def validate_test_case(test_case_data):
    """
    Validate if a test case is suitable for Playwright automation.
    
    Required fields for valid Playwright test case:
    - test_case_id or id
    - title or name
    - test_steps or steps
    - expected_result or expected
    """
    required_keys = {
        'test_case_id', 'id', 'title', 'name', 
        'test_steps', 'steps', 
        'expected_result', 'expected'
    }
    
    # Check for at least one identifier
    has_id = any(key in test_case_data for key in ['test_case_id', 'id', 'title', 'name'])
    
    # Check for steps
    has_steps = any(key in test_case_data for key in ['test_steps', 'steps'])
    
    # Check for expected result
    has_expected = any(key in test_case_data for key in ['expected_result', 'expected'])
    
    return has_id and has_steps and has_expected


def count_valid_test_cases(filepath):
    """Count valid Playwright test cases in an Excel file."""
    try:
        if filepath.suffix.lower() == '.xlsx':
            df = pd.read_excel(filepath, sheet_name=0)
        else:
            df = pd.read_excel(filepath)
        
        valid_count = 0
        for idx, row in df.iterrows():
            test_case_dict = row.to_dict()
            # Remove NaN values
            test_case_dict = {k: v for k, v in test_case_dict.items() if pd.notna(v)}
            
            if validate_test_case(test_case_dict):
                valid_count += 1
        
        return valid_count
    except Exception as e:
        print(f"Error validating {filepath}: {e}")
        return 0


def is_test_case_cleared(test_case_data):
    """
    Check if a test case is cleared for Playwright execution.
    
    Cleared test cases should have:
    - automation_candidate = True or 1 or 'Yes'
    - No missing required fields
    """
    automation_candidate = test_case_data.get('automation_candidate')
    
    if automation_candidate is None:
        return False
    
    # Check various True representations
    if isinstance(automation_candidate, bool):
        return automation_candidate
    if isinstance(automation_candidate, (int, float)):
        return automation_candidate == 1
    if isinstance(automation_candidate, str):
        return automation_candidate.lower() in ['true', 'yes', '1', 'y']
    
    return False


def count_cleared_test_cases(filepath):
    """Count test cases cleared for Playwright in an Excel file."""
    try:
        if filepath.suffix.lower() == '.xlsx':
            df = pd.read_excel(filepath, sheet_name=0)
        else:
            df = pd.read_excel(filepath)
        
        cleared_count = 0
        for idx, row in df.iterrows():
            test_case_dict = row.to_dict()
            # Remove NaN values
            test_case_dict = {k: v for k, v in test_case_dict.items() if pd.notna(v)}
            
            if is_test_case_cleared(test_case_dict):
                cleared_count += 1
        
        return cleared_count
    except Exception as e:
        print(f"Error counting cleared cases in {filepath}: {e}")
        return 0


def get_dashboard_stats():
    """Get all dashboard statistics."""
    excel_files = get_excel_files()
    
    stats = {
        "excel_file_count": len(excel_files),
        "total_test_cases": 0,
        "total_valid_test_cases": 0,
        "total_cleared_test_cases": 0,
        "files": [],
        "generated_test_count": 0,
        "last_updated": datetime.now().isoformat(),
    }
    
    # Count generated tests
    if GENERATED_DIR.exists():
        gen_files = list(GENERATED_DIR.glob("test_*.py"))
        stats["generated_test_count"] = len(gen_files)
    
    # Process each Excel file
    for excel_file in excel_files:
        total = count_test_cases_in_file(excel_file)
        valid = count_valid_test_cases(excel_file)
        cleared = count_cleared_test_cases(excel_file)
        
        stats["total_test_cases"] += total
        stats["total_valid_test_cases"] += valid
        stats["total_cleared_test_cases"] += cleared
        
        stats["files"].append({
            "name": excel_file.name,
            "path": str(excel_file.relative_to(BASE_DIR)),
            "total_test_cases": total,
            "valid_test_cases": valid,
            "cleared_test_cases": cleared,
            "last_modified": datetime.fromtimestamp(excel_file.stat().st_mtime).isoformat(),
        })
    
    return stats


@app.route("/")
def index():
    """Main dashboard page."""
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/api/stats")
def api_stats():
    """API endpoint for dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)


@app.route("/api/files")
def api_files():
    """API endpoint for list of Excel files."""
    excel_files = get_excel_files()
    files_info = []
    
    for excel_file in excel_files:
        files_info.append({
            "name": excel_file.name,
            "path": str(excel_file.relative_to(BASE_DIR)),
            "size": excel_file.stat().st_size,
            "last_modified": datetime.fromtimestamp(excel_file.stat().st_mtime).isoformat(),
            "total_test_cases": count_test_cases_in_file(excel_file),
            "valid_test_cases": count_valid_test_cases(excel_file),
            "cleared_test_cases": count_cleared_test_cases(excel_file),
        })
    
    return jsonify({"files": files_info, "count": len(files_info)})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """API endpoint to generate Playwright scripts from selected Excel file."""
    try:
        data = request.get_json()
        file_path = data.get("file_path")
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "No file path provided"
            }), 400
        
        # Resolve full file path
        full_path = BASE_DIR / file_path
        
        if not full_path.exists():
            return jsonify({
                "success": False,
                "error": f"File not found: {file_path}"
            }), 404
        
        # Read Excel file
        try:
            if full_path.suffix.lower() == '.xlsx':
                df = pd.read_excel(full_path, sheet_name=0)
            else:
                df = pd.read_excel(full_path)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Failed to read Excel file: {str(e)}"
            }), 400
        
        # Generate Playwright scripts
        generated_count = 0
        generated_files = []
        
        for idx, row in df.iterrows():
            test_case_dict = row.to_dict()
            # Remove NaN values
            test_case_dict = {k: v for k, v in test_case_dict.items() if pd.notna(v)}
            
            # Validate and generate script
            if validate_test_case(test_case_dict):
                try:
                    script_content = generate_playwright_script(test_case_dict, idx)
                    script_filename = GENERATED_DIR / f"test_{idx}_{test_case_dict.get('test_case_id', test_case_dict.get('id', idx))}.py"
                    
                    with open(script_filename, 'w') as f:
                        f.write(script_content)
                    
                    generated_count += 1
                    generated_files.append(script_filename.name)
                except Exception as e:
                    print(f"Error generating script for row {idx}: {e}")
                    traceback.print_exc()
        
        if generated_count == 0:
            return jsonify({
                "success": False,
                "error": "No valid test cases found in the selected file"
            }), 400
        
        return jsonify({
            "success": True,
            "generated_count": generated_count,
            "generated_files": generated_files,
            "message": f"Successfully generated {generated_count} Playwright script(s)"
        })
    
    except Exception as e:
        print(f"Error in generate endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


def generate_playwright_script(test_case, test_index):
    """Generate a Playwright script from a test case."""
    test_id = test_case.get('test_case_id', test_case.get('id', f'test_{test_index}'))
    title = test_case.get('title', test_case.get('name', f'Test {test_index}'))
    steps = test_case.get('test_steps', test_case.get('steps', ''))
    expected_result = test_case.get('expected_result', test_case.get('expected', ''))
    
    # Clean up steps and expected result
    steps_str = str(steps).strip()
    expected_str = str(expected_result).strip()
    
    script = f'''"""
Test Case: {title}
Test ID: {test_id}
Generated automatically from test case definition.
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.asyncio
async def test_{test_id.replace(' ', '_').lower()}(page: Page):
    """
    Test: {title}
    
    Steps:
    {steps_str}
    
    Expected Result:
    {expected_str}
    """
    # TODO: Implement test automation
    # Replace the following with your actual test steps
    
    # Example:
    # await page.goto("https://example.com")
    # await page.click("button.login")
    # assert await page.is_visible("text=Welcome")
    
    pass
'''
    
    return script


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8002, debug=False)
