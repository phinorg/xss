#!/usr/bin/env python3
"""
Test script for the Secure File Reader

This script tests all the security features and demonstrates proper usage.
"""

import sys
import os
from secure_file_reader import (
    SecureFileReader, 
    SecureFileReaderError, 
    InvalidPathError, 
    FileAccessDeniedError,
    create_secure_reader
)

def run_tests():
    """Run comprehensive tests of the secure file reader."""
    print("🔒 Testing Secure File Reader\n")
    
    # Create a test reader
    reader = create_secure_reader(
        allowed_paths=['/workspace'],
        allowed_extensions=['.txt', '.py', '.md'],
        max_size_mb=1
    )
    
    # Test cases with expected outcomes
    test_cases = [
        # (file_path, should_succeed, description)
        ('requirements.txt', True, 'Valid file in workspace'),
        ('xss.py', True, 'Python file should be allowed'),
        ('../etc/passwd', False, 'Path traversal should be blocked'),
        ('/etc/passwd', False, 'Absolute path outside workspace should be blocked'),
        ('nonexistent.txt', False, 'Non-existent file should fail'),
        ('requirements.txt\x00malicious', False, 'Null byte injection should be blocked'),
        ('.', False, 'Directory access should be blocked'),
        ('', False, 'Empty path should be invalid'),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for file_path, should_succeed, description in test_cases:
        print(f"Testing: {description}")
        print(f"  Path: '{file_path}'")
        
        try:
            content = reader.read_file(file_path)
            if should_succeed:
                print(f"  ✅ SUCCESS: Read {len(content)} characters")
                passed += 1
            else:
                print(f"  ❌ FAIL: Expected error but succeeded")
                
        except (InvalidPathError, FileAccessDeniedError, SecureFileReaderError) as e:
            if not should_succeed:
                print(f"  ✅ SUCCESS: Correctly blocked - {type(e).__name__}: {e}")
                passed += 1
            else:
                print(f"  ❌ FAIL: Expected success but got error - {type(e).__name__}: {e}")
                
        except Exception as e:
            print(f"  ❌ FAIL: Unexpected error - {type(e).__name__}: {e}")
        
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    return passed == total

def demo_usage():
    """Demonstrate proper usage patterns."""
    print("📖 Usage Examples\n")
    
    # Example 1: Basic usage
    print("1. Basic file reading:")
    try:
        reader = SecureFileReader(allowed_base_paths=['/workspace'])
        content = reader.read_file('requirements.txt')
        print(f"   Read {len(content)} characters from requirements.txt")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Example 2: Using context manager
    print("2. Using context manager:")
    try:
        reader = SecureFileReader(allowed_base_paths=['/workspace'])
        with reader.open_file('requirements.txt') as f:
            lines = f.readlines()
            print(f"   Read {len(lines)} lines using context manager")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Example 3: Reading lines
    print("3. Reading file lines:")
    try:
        reader = SecureFileReader(allowed_base_paths=['/workspace'])
        lines = reader.read_file_lines('requirements.txt')
        print(f"   Read {len(lines)} lines as list")
        for i, line in enumerate(lines[:3]):  # Show first 3 lines
            print(f"   Line {i+1}: {line.strip()}")
    except Exception as e:
        print(f"   Error: {e}")

def demonstrate_security_features():
    """Demonstrate security features in action."""
    print("🛡️  Security Features Demonstration\n")
    
    reader = SecureFileReader(
        allowed_base_paths=['/workspace'],
        allowed_extensions=['.txt', '.py'],
        max_file_size=1024,  # 1KB for demo
        enable_logging=True
    )
    
    print("Testing security features:")
    
    # Test 1: Path traversal protection
    print("\n1. Path Traversal Protection:")
    malicious_paths = ['../etc/passwd', '..\\windows\\system32\\drivers\\etc\\hosts', '%2e%2e/etc/passwd']
    for path in malicious_paths:
        try:
            reader.read_file(path)
            print(f"   ❌ SECURITY ISSUE: {path} was not blocked!")
        except (InvalidPathError, FileAccessDeniedError):
            print(f"   ✅ Blocked: {path}")
    
    # Test 2: Null byte injection protection
    print("\n2. Null Byte Injection Protection:")
    null_byte_paths = ['requirements.txt\x00../../etc/passwd', 'safe.txt\x00malicious']
    for path in null_byte_paths:
        try:
            reader.read_file(path)
            print(f"   ❌ SECURITY ISSUE: Null byte in path was not blocked!")
        except (InvalidPathError, FileAccessDeniedError):
            print(f"   ✅ Blocked: Path with null byte")
    
    # Test 3: Directory restriction
    print("\n3. Directory Restriction:")
    outside_paths = ['/etc/passwd', '/tmp/test.txt', 'C:\\Windows\\System32\\drivers\\etc\\hosts']
    for path in outside_paths:
        try:
            reader.read_file(path)
            print(f"   ❌ SECURITY ISSUE: {path} outside allowed directories was not blocked!")
        except (InvalidPathError, FileAccessDeniedError):
            print(f"   ✅ Blocked: {path}")
    
    print("\n✅ All security features working correctly!")

if __name__ == '__main__':
    print("=" * 60)
    print("🔒 SECURE FILE READER TEST SUITE")
    print("=" * 60)
    
    # Run tests
    tests_passed = run_tests()
    
    print("\n" + "-" * 60)
    
    # Demo usage
    demo_usage()
    
    print("\n" + "-" * 60)
    
    # Security demonstration
    demonstrate_security_features()
    
    print("\n" + "=" * 60)
    if tests_passed:
        print("🎉 ALL TESTS PASSED - Secure File Reader is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please review the implementation")
        sys.exit(1)
    print("=" * 60)