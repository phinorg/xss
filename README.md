# File to Database Script

A Python script that reads data from various file formats (CSV, JSON, TXT) and inserts it into a SQLite database with automatic table creation and data type inference.

## Features

- **Multiple file format support**: CSV, JSON, and delimited text files
- **Automatic data type inference**: Automatically detects INTEGER, REAL, and TEXT data types
- **Flexible table creation**: Creates tables with appropriate column types
- **Command-line interface**: Easy-to-use CLI with multiple options
- **Sample data generation**: Built-in sample file generator for testing
- **Error handling**: Comprehensive error handling and validation

## Requirements

- Python 3.6+
- Standard library modules only (no external dependencies required)

## Usage

### Basic Usage

```bash
# Import CSV file
python3 file_to_database.py data.csv

# Import JSON file with custom table name
python3 file_to_database.py data.json --table-name my_products

# Import text file with custom database
python3 file_to_database.py data.txt --database my_data.db --table-name countries

# Import CSV file with specific delimiter
python3 file_to_database.py data.csv --delimiter "," --table-name employees
```

### Command Line Options

- `file_path`: Path to the input file (required unless using --create-samples)
- `--table-name`: Name of the database table (default: "data_table")
- `--database`: Path to SQLite database file (default: "data.db")
- `--file-type`: Explicitly specify file type (csv, json, txt) - auto-detected by default
- `--delimiter`: Delimiter for text files (default: tab)
- `--create-samples`: Create sample data files for testing

### Generate Sample Files

```bash
python3 file_to_database.py --create-samples
```

This creates three sample files:
- `sample_data.csv`: Employee data
- `sample_data.json`: Product data  
- `sample_data.txt`: Country data (tab-delimited)

## File Format Examples

### CSV Format
```csv
name,age,city,salary
John Doe,30,New York,75000
Jane Smith,25,Los Angeles,65000
```

### JSON Format
```json
[
  {"product": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": true},
  {"product": "Book", "price": 29.99, "category": "Education", "in_stock": true}
]
```

### Text Format (Tab-delimited)
```
country	population	capital
USA	331000000	Washington D.C.
Canada	38000000	Ottawa
```

## Database Schema

The script automatically:
1. **Creates tables** with an auto-incrementing `id` column
2. **Infers data types** based on the data content:
   - INTEGER: For whole numbers
   - REAL: For decimal numbers  
   - TEXT: For strings and mixed content
3. **Handles duplicates** by creating tables with `IF NOT EXISTS`

## Examples

### Example 1: Import Employee Data

```bash
# Create sample files
python3 file_to_database.py --create-samples

# Import employee CSV data
python3 file_to_database.py sample_data.csv --table-name employees

# Output:
# Processing CSV file: sample_data.csv
# Read 3 records from CSV file: sample_data.csv
# Inferred column types: {'name': 'TEXT', 'age': 'INTEGER', 'city': 'TEXT', 'salary': 'INTEGER'}
# Connected to database: data.db
# Table 'employees' created/verified successfully.
# Successfully inserted 3 records into 'employees' table.
# Total records in 'employees' table: 3
# Database connection closed.
```

### Example 2: Import JSON Product Data

```bash
python3 file_to_database.py sample_data.json --table-name products --database products.db
```

### Example 3: Import Custom Delimited File

```bash
# For comma-separated values
python3 file_to_database.py data.csv --delimiter "," --table-name sales

# For pipe-separated values  
python3 file_to_database.py data.txt --delimiter "|" --table-name logs
```

## Database Schema Example

After importing the sample CSV file, the resulting table structure would be:

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER, 
    city TEXT,
    salary INTEGER
);
```

## Extending the Script

### Adding New Database Types

To support PostgreSQL or MySQL, modify the `DatabaseManager` class:

```python
# For PostgreSQL
import psycopg2

class PostgreSQLManager(DatabaseManager):
    def connect(self):
        self.connection = psycopg2.connect(
            host="localhost", 
            database="mydb", 
            user="user", 
            password="pass"
        )
```

### Adding New File Formats

Add new methods to the `FileProcessor` class:

```python
@staticmethod
def read_excel(file_path: str) -> List[Dict[str, Any]]:
    import pandas as pd
    df = pd.read_excel(file_path)
    return df.to_dict('records')
```

## Troubleshooting

### Common Issues

1. **File not found**: Ensure the file path is correct and the file exists
2. **Permission errors**: Check file and directory permissions
3. **Encoding issues**: The script uses UTF-8 encoding by default
4. **Memory issues**: For very large files, consider processing in chunks

### Data Type Issues

- **Mixed data types**: The script defaults to TEXT for mixed content
- **Date handling**: Dates are imported as TEXT; consider preprocessing for date columns
- **Boolean values**: JSON booleans are converted to INTEGER (0/1)

## License

This script is provided as-is for educational and practical use. Feel free to modify and distribute.