#!/usr/bin/env python3
"""
File to Database Script

This script reads data from various file formats (CSV, JSON, TXT) and inserts it into a database.
Supports SQLite by default, with easy extension to other databases like PostgreSQL or MySQL.
"""

import sqlite3
import csv
import json
import os
import sys
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime


class DatabaseManager:
    """Handles database operations including connection, table creation, and data insertion."""
    
    def __init__(self, db_path: str = "data.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
    
    def create_table(self, table_name: str, columns: Dict[str, str]):
        """
        Create a table with specified columns.
        
        Args:
            table_name: Name of the table to create
            columns: Dictionary mapping column names to their SQL types
        """
        try:
            # Create column definitions
            column_defs = []
            for col_name, col_type in columns.items():
                column_defs.append(f"{col_name} {col_type}")
            
            # Add an auto-incrementing ID column
            column_defs.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")
            
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            self.cursor.execute(sql)
            self.connection.commit()
            print(f"Table '{table_name}' created/verified successfully.")
            
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            sys.exit(1)
    
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]):
        """
        Insert data into the specified table.
        
        Args:
            table_name: Name of the table to insert data into
            data: List of dictionaries containing the data to insert
        """
        if not data:
            print("No data to insert.")
            return
        
        try:
            # Get column names from the first record (excluding 'id')
            columns = [col for col in data[0].keys() if col != 'id']
            placeholders = ', '.join(['?' for _ in columns])
            
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Prepare data for insertion
            values_list = []
            for record in data:
                values = [record.get(col) for col in columns]
                values_list.append(values)
            
            self.cursor.executemany(sql, values_list)
            self.connection.commit()
            print(f"Successfully inserted {len(data)} records into '{table_name}' table.")
            
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
            sys.exit(1)


class FileProcessor:
    """Handles reading and processing data from various file formats."""
    
    @staticmethod
    def read_csv(file_path: str) -> List[Dict[str, Any]]:
        """Read data from a CSV file."""
        data = []
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(dict(row))
            print(f"Read {len(data)} records from CSV file: {file_path}")
            return data
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            sys.exit(1)
    
    @staticmethod
    def read_json(file_path: str) -> List[Dict[str, Any]]:
        """Read data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
                
                # If it's a single object, wrap it in a list
                if isinstance(data, dict):
                    data = [data]
                elif not isinstance(data, list):
                    print("JSON file must contain a list of objects or a single object.")
                    sys.exit(1)
                
            print(f"Read {len(data)} records from JSON file: {file_path}")
            return data
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            sys.exit(1)
    
    @staticmethod
    def read_txt(file_path: str, delimiter: str = '\t') -> List[Dict[str, Any]]:
        """
        Read data from a text file with delimited values.
        
        Args:
            file_path: Path to the text file
            delimiter: Character used to separate values (default: tab)
        """
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as txtfile:
                lines = txtfile.readlines()
                
                if not lines:
                    print("Text file is empty.")
                    return data
                
                # First line contains headers
                headers = lines[0].strip().split(delimiter)
                
                # Process remaining lines
                for line_num, line in enumerate(lines[1:], start=2):
                    values = line.strip().split(delimiter)
                    if len(values) == len(headers):
                        record = dict(zip(headers, values))
                        data.append(record)
                    else:
                        print(f"Warning: Line {line_num} has {len(values)} values but expected {len(headers)}. Skipping.")
                
            print(f"Read {len(data)} records from text file: {file_path}")
            return data
        except Exception as e:
            print(f"Error reading text file: {e}")
            sys.exit(1)


def infer_column_types(data: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Infer SQL column types based on the data.
    
    Args:
        data: List of dictionaries containing the data
        
    Returns:
        Dictionary mapping column names to SQL types
    """
    if not data:
        return {}
    
    columns = {}
    
    for key in data[0].keys():
        # Sample values from this column
        sample_values = [record.get(key) for record in data[:100] if record.get(key) is not None]
        
        if not sample_values:
            columns[key] = "TEXT"
            continue
        
        # Try to determine the best type
        is_int = all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) for v in sample_values)
        is_float = all(isinstance(v, (int, float)) or 
                      (isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit()) 
                      for v in sample_values)
        
        if is_int:
            columns[key] = "INTEGER"
        elif is_float:
            columns[key] = "REAL"
        else:
            columns[key] = "TEXT"
    
    return columns


def create_sample_files():
    """Create sample data files for testing."""
    # Create sample CSV file
    csv_data = [
        ["name", "age", "city", "salary"],
        ["John Doe", "30", "New York", "75000"],
        ["Jane Smith", "25", "Los Angeles", "65000"],
        ["Bob Johnson", "35", "Chicago", "80000"]
    ]
    
    with open("sample_data.csv", "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)
    
    # Create sample JSON file
    json_data = [
        {"product": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": True},
        {"product": "Book", "price": 29.99, "category": "Education", "in_stock": True},
        {"product": "Chair", "price": 199.99, "category": "Furniture", "in_stock": False}
    ]
    
    with open("sample_data.json", "w") as jsonfile:
        json.dump(json_data, jsonfile, indent=2)
    
    # Create sample text file
    txt_data = [
        "country\tpopulation\tcapital",
        "USA\t331000000\tWashington D.C.",
        "Canada\t38000000\tOttawa",
        "Mexico\t129000000\tMexico City"
    ]
    
    with open("sample_data.txt", "w") as txtfile:
        txtfile.write("\n".join(txt_data))
    
    print("Sample files created: sample_data.csv, sample_data.json, sample_data.txt")


def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(description="Read data from files and insert into database")
    parser.add_argument("file_path", nargs='?', help="Path to the input file")
    parser.add_argument("--table-name", default="data_table", help="Name of the database table")
    parser.add_argument("--database", default="data.db", help="Path to the SQLite database file")
    parser.add_argument("--file-type", choices=["csv", "json", "txt"], 
                       help="File type (if not specified, will be inferred from extension)")
    parser.add_argument("--delimiter", default="\t", help="Delimiter for text files (default: tab)")
    parser.add_argument("--create-samples", action="store_true", 
                       help="Create sample data files for testing")
    
    args = parser.parse_args()
    
    # Create sample files if requested
    if args.create_samples:
        create_sample_files()
        return
    
    # Check if file_path is provided when not creating samples
    if not args.file_path:
        parser.error("file_path is required unless --create-samples is used")
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File '{args.file_path}' does not exist.")
        sys.exit(1)
    
    # Determine file type
    file_type = args.file_type
    if not file_type:
        ext = os.path.splitext(args.file_path)[1].lower()
        if ext == ".csv":
            file_type = "csv"
        elif ext == ".json":
            file_type = "json"
        elif ext in [".txt", ".tsv"]:
            file_type = "txt"
        else:
            print(f"Cannot determine file type from extension '{ext}'. Please specify --file-type.")
            sys.exit(1)
    
    print(f"Processing {file_type.upper()} file: {args.file_path}")
    
    # Read data from file
    processor = FileProcessor()
    if file_type == "csv":
        data = processor.read_csv(args.file_path)
    elif file_type == "json":
        data = processor.read_json(args.file_path)
    elif file_type == "txt":
        data = processor.read_txt(args.file_path, args.delimiter)
    
    if not data:
        print("No data found in file.")
        return
    
    # Infer column types
    columns = infer_column_types(data)
    print(f"Inferred column types: {columns}")
    
    # Connect to database and create table
    db_manager = DatabaseManager(args.database)
    db_manager.connect()
    
    try:
        db_manager.create_table(args.table_name, columns)
        db_manager.insert_data(args.table_name, data)
        
        # Display some statistics
        db_manager.cursor.execute(f"SELECT COUNT(*) FROM {args.table_name}")
        count = db_manager.cursor.fetchone()[0]
        print(f"Total records in '{args.table_name}' table: {count}")
        
    finally:
        db_manager.disconnect()
    
    print(f"Data successfully imported to database: {args.database}")


if __name__ == "__main__":
    main()