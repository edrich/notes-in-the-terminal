#!/usr/bin/env python3
"""
Test runner for the notes application.
Runs all tests and displays results.
"""
import sys
import unittest
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests(verbosity=2):
    """
    Run all tests in the tests directory.

    Args:
        verbosity: Level of output detail (0=quiet, 1=normal, 2=verbose)

    Returns:
        True if all tests passed, False otherwise
    """
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


def main():
    """Main entry point for test runner."""
    import argparse

    parser = argparse.ArgumentParser(description='Run tests for the notes application')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet output (minimal)')
    parser.add_argument('-t', '--test', metavar='TEST',
                       help='Run specific test module (e.g., test_storage)')

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # Run specific test or all tests
    if args.test:
        # Run specific test module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(f'tests.{args.test}')
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        success = result.wasSuccessful()
    else:
        # Run all tests
        success = run_tests(verbosity)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
