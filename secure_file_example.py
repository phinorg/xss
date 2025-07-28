#!/usr/bin/env python3
"""
Secure File Reader Integration Examples

This module demonstrates how to integrate the SecureFileReader with Flask
applications and provides practical usage examples.
"""

from flask import Flask, request, jsonify, render_template_string
from secure_file_reader import SecureFileReader, SecureFileReaderError, InvalidPathError, FileAccessDeniedError
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'secure-file-reader-demo'

# Initialize secure file reader with strict security settings
secure_reader = SecureFileReader(
    allowed_base_paths=['/workspace', '/tmp/safe_files'],  # Only allow specific directories
    allowed_extensions=['.txt', '.log', '.csv', '.json', '.py', '.md'],  # Whitelist file types
    max_file_size=5 * 1024 * 1024,  # 5MB max file size
    enable_logging=True
)

# HTML template for the demo interface
DEMO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Secure File Reader Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin: 20px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .form-group button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .form-group button:hover { background: #0056b3; }
        .result { margin: 20px 0; padding: 15px; border-radius: 4px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .file-content { background: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; margin: 10px 0; border-radius: 4px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-family: monospace; }
        .security-info { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 4px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Secure File Reader Demo</h1>
        
        <div class="security-info">
            <h3>Security Features Active:</h3>
            <ul>
                <li>✅ Path traversal protection (../ blocked)</li>
                <li>✅ Null byte injection protection</li>
                <li>✅ Directory restriction (only /workspace allowed)</li>
                <li>✅ File extension whitelist (.txt, .log, .csv, .json, .py, .md)</li>
                <li>✅ File size limit (5MB max)</li>
                <li>✅ Comprehensive logging</li>
            </ul>
        </div>
        
        <form method="POST" action="/read_file">
            <div class="form-group">
                <label for="file_path">File Path to Read:</label>
                <input type="text" id="file_path" name="file_path" 
                       placeholder="e.g., requirements.txt or subdir/file.txt"
                       value="{{ file_path or '' }}">
            </div>
            <div class="form-group">
                <button type="submit">🔍 Read File Securely</button>
            </div>
        </form>
        
        {% if result %}
        <div class="result {{ result.status }}">
            <h3>{{ "✅ Success" if result.status == "success" else "❌ Error" }}</h3>
            <p><strong>Message:</strong> {{ result.message }}</p>
            {% if result.content %}
            <div class="file-content">{{ result.content }}</div>
            {% endif %}
        </div>
        {% endif %}
        
        <h2>Example Test Cases</h2>
        <p>Try these examples to see the security features in action:</p>
        <ul>
            <li><code>requirements.txt</code> - ✅ Should work (valid file)</li>
            <li><code>xss.py</code> - ✅ Should work (Python file)</li>
            <li><code>../etc/passwd</code> - ❌ Blocked (path traversal)</li>
            <li><code>/etc/passwd</code> - ❌ Blocked (outside allowed paths)</li>
            <li><code>nonexistent.txt</code> - ❌ File not found</li>
            <li><code>requirements.txt\x00malicious</code> - ❌ Null byte injection blocked</li>
        </ul>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main demo page."""
    return render_template_string(DEMO_TEMPLATE)

@app.route('/read_file', methods=['POST'])
def read_file_endpoint():
    """Secure file reading endpoint."""
    file_path = request.form.get('file_path', '').strip()
    
    if not file_path:
        return render_template_string(DEMO_TEMPLATE, 
                                    result={
                                        'status': 'error',
                                        'message': 'Please provide a file path',
                                        'content': None
                                    },
                                    file_path=file_path)
    
    try:
        # Attempt to read the file securely
        content = secure_reader.read_file(file_path)
        
        # Limit display to first 2000 characters for UI
        display_content = content[:2000]
        if len(content) > 2000:
            display_content += f"\n\n... (truncated, total length: {len(content)} characters)"
        
        return render_template_string(DEMO_TEMPLATE,
                                    result={
                                        'status': 'success',
                                        'message': f'Successfully read file: {file_path} ({len(content)} characters)',
                                        'content': display_content
                                    },
                                    file_path=file_path)
                                    
    except InvalidPathError as e:
        return render_template_string(DEMO_TEMPLATE,
                                    result={
                                        'status': 'error',
                                        'message': f'Invalid path: {str(e)}',
                                        'content': None
                                    },
                                    file_path=file_path)
                                    
    except FileAccessDeniedError as e:
        return render_template_string(DEMO_TEMPLATE,
                                    result={
                                        'status': 'error',
                                        'message': f'Access denied: {str(e)}',
                                        'content': None
                                    },
                                    file_path=file_path)
                                    
    except SecureFileReaderError as e:
        return render_template_string(DEMO_TEMPLATE,
                                    result={
                                        'status': 'error',
                                        'message': f'File reading error: {str(e)}',
                                        'content': None
                                    },
                                    file_path=file_path)
                                    
    except Exception as e:
        app.logger.error(f"Unexpected error reading file {file_path}: {e}")
        return render_template_string(DEMO_TEMPLATE,
                                    result={
                                        'status': 'error',
                                        'message': 'An unexpected error occurred',
                                        'content': None
                                    },
                                    file_path=file_path)

@app.route('/api/read_file', methods=['POST'])
def api_read_file():
    """JSON API endpoint for secure file reading."""
    data = request.get_json()
    
    if not data or 'file_path' not in data:
        return jsonify({
            'success': False,
            'error': 'file_path is required',
            'error_type': 'invalid_request'
        }), 400
    
    file_path = data['file_path']
    encoding = data.get('encoding', 'utf-8')
    binary_mode = data.get('binary', False)
    
    try:
        if binary_mode:
            content = secure_reader.read_file_binary(file_path)
            # Convert to base64 for JSON response
            import base64
            content_b64 = base64.b64encode(content).decode('ascii')
            return jsonify({
                'success': True,
                'content': content_b64,
                'content_type': 'binary',
                'size': len(content),
                'file_path': file_path
            })
        else:
            content = secure_reader.read_file(file_path, encoding=encoding)
            return jsonify({
                'success': True,
                'content': content,
                'content_type': 'text',
                'size': len(content),
                'file_path': file_path
            })
            
    except (InvalidPathError, FileAccessDeniedError) as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'file_path': file_path
        }), 403
        
    except SecureFileReaderError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'file_path': file_path
        }), 500
        
    except Exception as e:
        app.logger.error(f"Unexpected error in API: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_type': 'unexpected_error'
        }), 500

@app.route('/api/list_allowed_paths')
def api_list_allowed_paths():
    """API endpoint to list allowed base paths and extensions."""
    return jsonify({
        'allowed_base_paths': [str(path) for path in secure_reader.allowed_base_paths],
        'allowed_extensions': secure_reader.allowed_extensions,
        'max_file_size': secure_reader.max_file_size,
        'max_file_size_mb': secure_reader.max_file_size / (1024 * 1024)
    })


def demonstrate_cli_usage():
    """Demonstrate command-line usage of the secure file reader."""
    print("=== Secure File Reader CLI Demo ===\n")
    
    # Create different reader configurations for different use cases
    
    # 1. Strict reader for production
    strict_reader = SecureFileReader(
        allowed_base_paths=['/workspace'],
        allowed_extensions=['.txt', '.log'],
        max_file_size=1024 * 1024,  # 1MB
        enable_logging=True
    )
    
    # 2. Development reader with more flexibility
    dev_reader = SecureFileReader(
        allowed_base_paths=['/workspace', '/tmp'],
        allowed_extensions=['.txt', '.py', '.json', '.md', '.log'],
        max_file_size=10 * 1024 * 1024,  # 10MB
        enable_logging=True
    )
    
    # Test different scenarios
    test_cases = [
        ("requirements.txt", strict_reader, "Strict reader"),
        ("xss.py", dev_reader, "Development reader"),
        ("../etc/passwd", strict_reader, "Path traversal attempt"),
        ("nonexistent.txt", dev_reader, "Non-existent file"),
    ]
    
    for file_path, reader, scenario in test_cases:
        print(f"\n--- Testing: {scenario} ---")
        print(f"File path: {file_path}")
        
        try:
            content = reader.read_file(file_path)
            print(f"✅ Success: Read {len(content)} characters")
            if len(content) < 200:
                print(f"Content preview: {content[:100]}...")
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")


if __name__ == '__main__':
    # Run CLI demo if executed directly
    demonstrate_cli_usage()
    
    # Start Flask app
    print("\n=== Starting Flask Demo Server ===")
    print("Visit http://localhost:5000 to see the web interface")
    print("API endpoint available at http://localhost:5000/api/read_file")
    
    app.run(debug=True, host='0.0.0.0', port=5000)