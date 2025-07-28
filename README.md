# 🔒 Secure Python File Reader

A comprehensive, production-ready Python module for securely reading user-provided file paths. This implementation addresses common security vulnerabilities and provides multiple layers of protection against file system attacks.

## 🛡️ Security Features

### Core Protections

- **Path Traversal Prevention**: Blocks `../` and `..\\` patterns, including URL-encoded variants
- **Null Byte Injection Protection**: Removes null bytes that could bypass security checks
- **Directory Restriction**: Confines file access to explicitly allowed base directories
- **File Extension Whitelist**: Optional restriction to specific file types
- **File Size Limits**: Prevents reading of excessively large files
- **Absolute Path Validation**: Ensures paths resolve to expected locations
- **Symbolic Link Resolution**: Properly handles and validates symbolic links
- **Comprehensive Logging**: Security events are logged for monitoring

### Attack Vectors Mitigated

- **Directory Traversal**: `../../../etc/passwd`
- **Null Byte Injection**: `safe.txt\x00../../etc/passwd`
- **URL Encoding Bypass**: `%2e%2e%2f` (../)
- **Windows Path Traversal**: `..\\..\\windows\\system32`
- **Absolute Path Bypass**: `/etc/passwd`
- **Symlink Attacks**: Malicious symbolic links
- **Resource Exhaustion**: Large file attacks

## 📋 Requirements

- Python 3.6+
- No external dependencies for core functionality
- Flask (optional, for web demo)

## 🚀 Quick Start

### Basic Usage

```python
from secure_file_reader import SecureFileReader

# Create a secure reader with default settings
reader = SecureFileReader(
    allowed_base_paths=['/safe/directory'],
    allowed_extensions=['.txt', '.log', '.csv'],
    max_file_size=5 * 1024 * 1024  # 5MB
)

# Read a file securely
try:
    content = reader.read_file('user_provided_path.txt')
    print(f"File content: {content}")
except Exception as e:
    print(f"Security violation or error: {e}")
```

### Convenience Function

```python
from secure_file_reader import create_secure_reader

# Quick setup with common defaults
reader = create_secure_reader(
    allowed_paths=['/workspace', '/uploads'],
    allowed_extensions=['.txt', '.log', '.json'],
    max_size_mb=10
)

content = reader.read_file('user_file.txt')
```

### Context Manager Usage

```python
# Use context manager for automatic resource cleanup
with reader.open_file('data.txt') as f:
    for line in f:
        process_line(line)
```

## 🔧 API Reference

### SecureFileReader Class

#### Constructor Parameters

- `allowed_base_paths` (List[str], optional): Allowed base directories. Defaults to current working directory.
- `allowed_extensions` (List[str], optional): Allowed file extensions. If None, all extensions are allowed.
- `max_file_size` (int): Maximum file size in bytes. Default: 10MB.
- `enable_logging` (bool): Enable security logging. Default: True.

#### Methods

##### `read_file(file_path: str, encoding: str = 'utf-8') -> str`
Read entire file content as a string.

##### `read_file_lines(file_path: str, encoding: str = 'utf-8') -> List[str]`
Read file and return lines as a list.

##### `read_file_binary(file_path: str) -> bytes`
Read file in binary mode.

##### `open_file(file_path: str, mode: str = 'r', encoding: str = 'utf-8')`
Context manager for file operations.

### Exception Classes

- `SecureFileReaderError`: Base exception class
- `InvalidPathError`: Raised for invalid or malicious paths
- `FileAccessDeniedError`: Raised when file access is denied

## 🌐 Flask Integration Example

```python
from flask import Flask, request, jsonify
from secure_file_reader import SecureFileReader

app = Flask(__name__)

# Initialize secure reader
secure_reader = SecureFileReader(
    allowed_base_paths=['/app/uploads'],
    allowed_extensions=['.txt', '.log', '.csv'],
    max_file_size=5 * 1024 * 1024
)

@app.route('/read_file', methods=['POST'])
def read_file_endpoint():
    file_path = request.json.get('file_path')
    
    try:
        content = secure_reader.read_file(file_path)
        return jsonify({
            'success': True,
            'content': content,
            'size': len(content)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 403
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_secure_reader.py
```

This will test:
- All security features
- Valid file operations
- Error handling
- Different usage patterns

## 🎯 Configuration Examples

### Production Configuration (Strict)

```python
# Maximum security for production
production_reader = SecureFileReader(
    allowed_base_paths=['/var/app/data'],
    allowed_extensions=['.txt', '.log'],
    max_file_size=1024 * 1024,  # 1MB
    enable_logging=True
)
```

### Development Configuration (Flexible)

```python
# More permissive for development
dev_reader = SecureFileReader(
    allowed_base_paths=['/workspace', '/tmp/dev'],
    allowed_extensions=['.txt', '.py', '.json', '.md', '.log'],
    max_file_size=10 * 1024 * 1024,  # 10MB
    enable_logging=True
)
```

### User Upload Handler

```python
# For handling user uploads
upload_reader = SecureFileReader(
    allowed_base_paths=['/uploads/user_files'],
    allowed_extensions=['.txt', '.csv', '.json'],
    max_file_size=5 * 1024 * 1024,  # 5MB
    enable_logging=True
)
```

## 🔍 Web Demo

A complete Flask web application demonstrating all security features is included:

```bash
python3 secure_file_example.py
```

Visit `http://localhost:5000` to interact with the secure file reader through a web interface.

### API Endpoints

- `POST /read_file` - HTML form interface
- `POST /api/read_file` - JSON API endpoint
- `GET /api/list_allowed_paths` - Configuration information

### API Usage Example

```bash
# Test the JSON API
curl -X POST http://localhost:5000/api/read_file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "requirements.txt"}'
```

## 🚨 Security Best Practices

### 1. Principle of Least Privilege
```python
# Only allow access to specific directories
reader = SecureFileReader(
    allowed_base_paths=['/app/public_files'],  # Narrow scope
    allowed_extensions=['.txt'],  # Limited file types
    max_file_size=1024 * 1024  # Reasonable size limit
)
```

### 2. Input Validation
```python
def safe_read_user_file(user_path: str):
    # Additional validation before using secure reader
    if not user_path or len(user_path) > 255:
        raise ValueError("Invalid file path length")
    
    if any(char in user_path for char in ['<', '>', '|', '*', '?']):
        raise ValueError("Invalid characters in file path")
    
    return reader.read_file(user_path)
```

### 3. Error Handling
```python
try:
    content = reader.read_file(user_provided_path)
    # Process content...
except InvalidPathError as e:
    logger.warning(f"Invalid path attempted: {user_provided_path}")
    return "Invalid file path"
except FileAccessDeniedError as e:
    logger.warning(f"Unauthorized access attempted: {user_provided_path}")
    return "Access denied"
except SecureFileReaderError as e:
    logger.error(f"File reading error: {e}")
    return "File could not be read"
```

### 4. Logging and Monitoring
```python
import logging

# Configure security logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/security.log'),
        logging.StreamHandler()
    ]
)
```

## 📊 Performance Considerations

- **File Size Limits**: Set appropriate limits to prevent memory exhaustion
- **Path Validation**: Validation is performed before file operations
- **Caching**: Consider caching file metadata for frequently accessed files
- **Async Support**: Can be easily adapted for async frameworks

## 🔧 Customization

### Custom Validators

```python
class CustomSecureReader(SecureFileReader):
    def _validate_path(self, file_path: str):
        # Add custom validation logic
        if 'forbidden_pattern' in file_path.lower():
            raise InvalidPathError("Forbidden pattern detected")
        
        return super()._validate_path(file_path)
```

### Additional Security Checks

```python
def create_enterprise_reader():
    reader = SecureFileReader(
        allowed_base_paths=['/enterprise/data'],
        allowed_extensions=['.txt', '.csv'],
        max_file_size=2 * 1024 * 1024
    )
    
    # Add additional enterprise-specific validation
    original_validate = reader._validate_path
    
    def enterprise_validate(file_path):
        # Check against enterprise policies
        if not is_authorized_for_file(file_path):
            raise FileAccessDeniedError("User not authorized for this file")
        return original_validate(file_path)
    
    reader._validate_path = enterprise_validate
    return reader
```

## 🐛 Troubleshooting

### Common Issues

1. **FileAccessDeniedError**: Check that the file is within allowed directories
2. **InvalidPathError**: Ensure the path doesn't contain suspicious patterns
3. **File not found**: Verify the file exists and is readable
4. **Permission denied**: Check file system permissions

### Debug Mode

```python
import logging
logging.getLogger('secure_file_reader').setLevel(logging.DEBUG)
```

## 📚 Additional Resources

- [OWASP Path Traversal Guide](https://owasp.org/www-community/attacks/Path_Traversal)
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)

## 📄 License

This code is provided as-is for educational and production use. Please review and test thoroughly before deploying in production environments.

## 🤝 Contributing

Contributions are welcome! Please ensure all security features are maintained and add appropriate tests for new functionality.

---

**⚠️ Security Notice**: While this implementation addresses many common attack vectors, security is an ongoing process. Always keep your dependencies updated and follow current security best practices for your specific use case.