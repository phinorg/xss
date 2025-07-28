#!/usr/bin/env python3
"""
Secure File Reader Module

This module provides secure methods for reading files based on user-provided paths.
It implements multiple security measures to prevent common file system attacks.
"""

import os
import pathlib
import logging
from typing import Optional, List, Union
from contextlib import contextmanager


class SecureFileReaderError(Exception):
    """Base exception for secure file reader errors."""
    pass


class FileAccessDeniedError(SecureFileReaderError):
    """Raised when file access is denied due to security restrictions."""
    pass


class InvalidPathError(SecureFileReaderError):
    """Raised when the provided path is invalid or malicious."""
    pass


class SecureFileReader:
    """
    A secure file reader that validates and sanitizes user-provided file paths
    before attempting to read files.
    """
    
    def __init__(self, 
                 allowed_base_paths: Optional[List[str]] = None,
                 allowed_extensions: Optional[List[str]] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB default
                 enable_logging: bool = True):
        """
        Initialize the SecureFileReader.
        
        Args:
            allowed_base_paths: List of allowed base directories. If None, uses current working directory.
            allowed_extensions: List of allowed file extensions (e.g., ['.txt', '.log']). If None, all extensions allowed.
            max_file_size: Maximum allowed file size in bytes.
            enable_logging: Whether to enable security event logging.
        """
        self.allowed_base_paths = self._normalize_base_paths(allowed_base_paths)
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
        self.max_file_size = max_file_size
        
        if enable_logging:
            self._setup_logging()
    
    def _setup_logging(self):
        """Setup security logging."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _normalize_base_paths(self, base_paths: Optional[List[str]]) -> List[pathlib.Path]:
        """Normalize and resolve base paths."""
        if base_paths is None:
            base_paths = [os.getcwd()]
        
        normalized_paths = []
        for path in base_paths:
            try:
                # Resolve to absolute path and normalize
                resolved_path = pathlib.Path(path).resolve()
                if resolved_path.exists() and resolved_path.is_dir():
                    normalized_paths.append(resolved_path)
                else:
                    self.logger.warning(f"Base path does not exist or is not a directory: {path}")
            except (OSError, ValueError) as e:
                self.logger.warning(f"Invalid base path {path}: {e}")
        
        if not normalized_paths:
            # Fallback to current working directory
            normalized_paths.append(pathlib.Path.cwd())
        
        return normalized_paths
    
    def _validate_path(self, file_path: str) -> pathlib.Path:
        """
        Validate and sanitize the user-provided file path.
        
        Args:
            file_path: User-provided file path string.
            
        Returns:
            Validated and resolved pathlib.Path object.
            
        Raises:
            InvalidPathError: If the path is invalid or potentially malicious.
            FileAccessDeniedError: If the path is outside allowed directories.
        """
        if not file_path or not isinstance(file_path, str):
            raise InvalidPathError("File path must be a non-empty string")
        
        # Remove null bytes and other problematic characters
        sanitized_path = file_path.replace('\x00', '').strip()
        
        if not sanitized_path:
            raise InvalidPathError("File path is empty after sanitization")
        
        # Check for suspicious patterns
        suspicious_patterns = ['../', '..\\', '%2e%2e', '%2e%2e%2f', '%2e%2e%5c']
        path_lower = sanitized_path.lower()
        
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                self.logger.warning(f"Suspicious path pattern detected: {file_path}")
                raise InvalidPathError(f"Path contains suspicious pattern: {pattern}")
        
        try:
            # Convert to Path object and resolve
            path_obj = pathlib.Path(sanitized_path)
            
            # If it's a relative path, we'll validate it against base paths later
            if path_obj.is_absolute():
                resolved_path = path_obj.resolve()
            else:
                # For relative paths, we'll check against each base path
                resolved_path = None
                for base_path in self.allowed_base_paths:
                    try:
                        candidate_path = (base_path / path_obj).resolve()
                        # Verify the resolved path is within the base path
                        if self._is_within_base_path(candidate_path, base_path):
                            resolved_path = candidate_path
                            break
                    except (OSError, ValueError):
                        continue
                
                if resolved_path is None:
                    raise FileAccessDeniedError(
                        "File path is not accessible within any allowed base directory"
                    )
            
        except (OSError, ValueError) as e:
            raise InvalidPathError(f"Invalid file path: {e}")
        
        return resolved_path
    
    def _is_within_base_path(self, file_path: pathlib.Path, base_path: pathlib.Path) -> bool:
        """
        Check if the file path is within the allowed base path.
        
        Args:
            file_path: The resolved file path to check.
            base_path: The base path to check against.
            
        Returns:
            True if file_path is within base_path, False otherwise.
        """
        try:
            file_path.relative_to(base_path)
            return True
        except ValueError:
            return False
    
    def _validate_file_access(self, file_path: pathlib.Path) -> None:
        """
        Validate that the file can be safely accessed.
        
        Args:
            file_path: The resolved file path to validate.
            
        Raises:
            FileAccessDeniedError: If file access is denied.
            InvalidPathError: If the file doesn't meet requirements.
        """
        # Check if file exists and is a regular file
        if not file_path.exists():
            raise FileAccessDeniedError(f"File does not exist: {file_path}")
        
        if not file_path.is_file():
            raise FileAccessDeniedError(f"Path is not a regular file: {file_path}")
        
        # Check if file is within allowed base paths
        path_allowed = False
        for base_path in self.allowed_base_paths:
            if self._is_within_base_path(file_path, base_path):
                path_allowed = True
                break
        
        if not path_allowed:
            self.logger.warning(f"Attempted access to file outside allowed paths: {file_path}")
            raise FileAccessDeniedError(
                "File is outside allowed base directories"
            )
        
        # Check file extension if restrictions are in place
        if self.allowed_extensions:
            file_extension = file_path.suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise FileAccessDeniedError(
                    f"File extension '{file_extension}' is not allowed. "
                    f"Allowed extensions: {self.allowed_extensions}"
                )
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise FileAccessDeniedError(
                    f"File size ({file_size} bytes) exceeds maximum allowed size "
                    f"({self.max_file_size} bytes)"
                )
        except OSError as e:
            raise FileAccessDeniedError(f"Cannot access file metadata: {e}")
    
    @contextmanager
    def open_file(self, file_path: str, mode: str = 'r', encoding: str = 'utf-8'):
        """
        Securely open a file with context manager support.
        
        Args:
            file_path: User-provided file path.
            mode: File open mode (default: 'r').
            encoding: File encoding (default: 'utf-8').
            
        Yields:
            File object.
            
        Raises:
            SecureFileReaderError: If file cannot be safely opened.
        """
        # Validate only read modes for security
        if 'w' in mode or 'a' in mode or 'x' in mode or '+' in mode:
            raise InvalidPathError("Only read modes are allowed for security")
        
        validated_path = self._validate_path(file_path)
        self._validate_file_access(validated_path)
        
        self.logger.info(f"Opening file for reading: {validated_path}")
        
        try:
            with open(validated_path, mode, encoding=encoding) as file:
                yield file
        except (OSError, UnicodeDecodeError) as e:
            raise SecureFileReaderError(f"Error reading file: {e}")
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Securely read the entire contents of a file.
        
        Args:
            file_path: User-provided file path.
            encoding: File encoding (default: 'utf-8').
            
        Returns:
            File contents as string.
            
        Raises:
            SecureFileReaderError: If file cannot be safely read.
        """
        with self.open_file(file_path, 'r', encoding) as file:
            return file.read()
    
    def read_file_lines(self, file_path: str, encoding: str = 'utf-8') -> List[str]:
        """
        Securely read a file and return its lines as a list.
        
        Args:
            file_path: User-provided file path.
            encoding: File encoding (default: 'utf-8').
            
        Returns:
            List of file lines.
            
        Raises:
            SecureFileReaderError: If file cannot be safely read.
        """
        with self.open_file(file_path, 'r', encoding) as file:
            return file.readlines()
    
    def read_file_binary(self, file_path: str) -> bytes:
        """
        Securely read a file in binary mode.
        
        Args:
            file_path: User-provided file path.
            
        Returns:
            File contents as bytes.
            
        Raises:
            SecureFileReaderError: If file cannot be safely read.
        """
        with self.open_file(file_path, 'rb', encoding=None) as file:
            return file.read()


def create_secure_reader(allowed_paths: Optional[List[str]] = None,
                        allowed_extensions: Optional[List[str]] = None,
                        max_size_mb: int = 10) -> SecureFileReader:
    """
    Convenience function to create a SecureFileReader instance.
    
    Args:
        allowed_paths: List of allowed base directories.
        allowed_extensions: List of allowed file extensions.
        max_size_mb: Maximum file size in megabytes.
        
    Returns:
        Configured SecureFileReader instance.
    """
    return SecureFileReader(
        allowed_base_paths=allowed_paths,
        allowed_extensions=allowed_extensions,
        max_file_size=max_size_mb * 1024 * 1024
    )


# Example usage and demonstration
if __name__ == "__main__":
    # Example 1: Basic secure file reading
    print("=== Secure File Reader Demo ===\n")
    
    # Create a secure reader with current directory as allowed base
    reader = create_secure_reader(
        allowed_paths=["/workspace"],  # Only allow files in workspace
        allowed_extensions=['.txt', '.py', '.md', '.log'],  # Only specific extensions
        max_size_mb=5  # 5MB max file size
    )
    
    # Example 2: Safe file reading with error handling
    def safe_read_file(file_path: str) -> None:
        """Demonstrate safe file reading with proper error handling."""
        try:
            print(f"Attempting to read: {file_path}")
            content = reader.read_file(file_path)
            print(f"Successfully read {len(content)} characters")
            print(f"First 100 characters: {content[:100]}...")
            print()
            
        except InvalidPathError as e:
            print(f"❌ Invalid path: {e}")
        except FileAccessDeniedError as e:
            print(f"❌ Access denied: {e}")
        except SecureFileReaderError as e:
            print(f"❌ File reading error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        print()
    
    # Test cases
    test_files = [
        "requirements.txt",  # Should work
        "xss.py",           # Should work
        "../etc/passwd",    # Should be blocked
        "nonexistent.txt",  # Should fail
        "requirements.txt\x00malicious",  # Should be sanitized
    ]
    
    for test_file in test_files:
        safe_read_file(test_file)