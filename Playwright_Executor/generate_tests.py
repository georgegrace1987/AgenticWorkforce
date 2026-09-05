"""
Quick helper script to generate Playwright tests.

Usage:
    python generate_tests.py sample_test_input.json
    python generate_tests.py sample_test_input.json --output my_tests.py
    python generate_tests.py --batch              # Process all JSON files
"""

import argparse
import sys
import logging
from pathlib import Path
from playwright_test_generator import PlaywrightTestGenerator

logger = logging.getLogger(__name__)


def generate_single(input_file: str, output_file: str = None):
    """Generate tests from a single input file."""
    generator = PlaywrightTestGenerator()
    
    try:
        result = generator.generate_and_save(input_file, output_file)
        print(f"\n✓ Success! Generated: {result}")
        return True
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print(f"  Available files in TestCases/:")
        test_dir = generator.test_cases_dir
        if test_dir.exists():
            for f in test_dir.glob("*.json"):
                print(f"    - {f.name}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def generate_batch():
    """Generate tests from all JSON files in TestCases directory."""
    generator = PlaywrightTestGenerator()
    test_dir = generator.test_cases_dir
    
    if not test_dir.exists():
        print(f"✗ TestCases directory not found: {test_dir}")
        return False
    
    json_files = list(test_dir.glob("*.json"))
    
    if not json_files:
        print(f"✗ No JSON files found in {test_dir}")
        return False
    
    print(f"\nProcessing {len(json_files)} test case file(s)...\n")
    
    success_count = 0
    for json_file in json_files:
        try:
            result = generator.generate_and_save(json_file.name)
            print(f"✓ {json_file.name} → {Path(result).name}")
            success_count += 1
        except Exception as e:
            print(f"✗ {json_file.name}: {e}")
    
    print(f"\n{success_count}/{len(json_files)} files generated successfully")
    return success_count == len(json_files)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Playwright tests from JSON test case definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_tests.py sample_test_input.json
  python generate_tests.py sample_test_input.json --output my_tests.py
  python generate_tests.py --batch
        """
    )
    
    parser.add_argument(
        "input",
        nargs="?",
        help="Input JSON file with test cases"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output test file name (auto-generated if not specified)"
    )
    
    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="Process all JSON files in TestCases/ directory"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available test case files"
    )
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        generator = PlaywrightTestGenerator()
        test_dir = generator.test_cases_dir
        print(f"\nTest case files in {test_dir}:\n")
        
        if test_dir.exists():
            json_files = list(test_dir.glob("*.json"))
            if json_files:
                for f in json_files:
                    size = f.stat().st_size
                    print(f"  {f.name:40s} ({size:,} bytes)")
            else:
                print("  No JSON files found")
        else:
            print(f"  Directory not found")
        return
    
    # Handle batch processing
    if args.batch:
        success = generate_batch()
        sys.exit(0 if success else 1)
    
    # Handle single file generation
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    success = generate_single(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
