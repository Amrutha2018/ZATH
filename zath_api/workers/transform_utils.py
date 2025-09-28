"""
Transformation utilities module for data processing operations.

This module provides functions for common data transformation tasks including
JSON flattening, CSV parsing, record filtering, and data aggregation.
"""

import csv
import io
from typing import Dict, List, Any, Union
from decimal import Decimal, InvalidOperation


def flatten_json(data: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Flatten a nested JSON dictionary.
    
    Args:
        data: The nested dictionary to flatten
        parent_key: The parent key for nested structures (used internally)
        sep: Separator to use between nested keys
        
    Returns:
        A flattened dictionary with dot-separated keys
        
    Raises:
        TypeError: If data is not a dictionary
        ValueError: If data contains invalid nested structures
        
    Examples:
        >>> flatten_json({'a': {'b': 1, 'c': 2}})
        {'a.b': 1, 'c': 2}
        
        >>> flatten_json({'x': [1, 2, 3]})
        {'x': [1, 2, 3]}
    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data).__name__}")
    
    items = []
    
    for key, value in data.items():
        if not isinstance(key, str):
            raise ValueError(f"Dictionary keys must be strings, got {type(key).__name__}")
            
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            items.extend(flatten_json(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # Handle lists - keep as is for now, could be extended to flatten list items
            items.append((new_key, value))
        else:
            # Primitive values
            items.append((new_key, value))
    
    return dict(items)


def csv_to_json(csv_content: str, delimiter: str = ',') -> List[Dict[str, Any]]:
    """
    Parse CSV content into a list of dictionaries.
    
    Args:
        csv_content: The CSV content as a string
        delimiter: The delimiter character to use for parsing
        
    Returns:
        A list of dictionaries where each dictionary represents a row
        
    Raises:
        ValueError: If CSV content is empty or invalid
        TypeError: If delimiter is not a string
        
    Examples:
        >>> csv_to_json("name,age\\nJohn,25\\nJane,30")
        [{'name': 'John', 'age': '25'}, {'name': 'Jane', 'age': '30'}]
        
        >>> csv_to_json("a;b;c\\n1;2;3", delimiter=';')
        [{'a': '1', 'b': '2', 'c': '3'}]
    """
    if not isinstance(csv_content, str):
        raise TypeError(f"Expected string, got {type(csv_content).__name__}")
    
    if not isinstance(delimiter, str):
        raise TypeError(f"Expected string delimiter, got {type(delimiter).__name__}")
    
    if not csv_content.strip():
        raise ValueError("CSV content cannot be empty")
    
    if len(delimiter) != 1:
        raise ValueError("Delimiter must be a single character")
    
    try:
        # Use StringIO to read CSV from string
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        
        # Convert to list of dictionaries
        result = list(reader)
        
        if not result:
            raise ValueError("CSV content contains no data rows")
            
        return result
        
    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")


def filter_records(records: List[Dict[str, Any]], **criteria) -> List[Dict[str, Any]]:
    """
    Filter records based on exact key-value matches.
    
    Args:
        records: List of dictionaries to filter
        **criteria: Key-value pairs for filtering criteria
        
    Returns:
        A list of records that match all criteria
        
    Raises:
        TypeError: If records is not a list or contains non-dictionary items
        ValueError: If criteria is empty
        
    Examples:
        >>> records = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
        >>> filter_records(records, age=25)
        [{'name': 'John', 'age': 25}]
        
        >>> filter_records(records, name='Jane', age=30)
        [{'name': 'Jane', 'age': 30}]
    """
    if not isinstance(records, list):
        raise TypeError(f"Expected list, got {type(records).__name__}")
    
    if not criteria:
        raise ValueError("At least one filter criterion must be provided")
    
    # Validate that all items in records are dictionaries
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(f"Record at index {i} is not a dictionary, got {type(record).__name__}")
    
    filtered_records = []
    
    for record in records:
        # Check if record matches all criteria
        matches = True
        for key, value in criteria.items():
            if key not in record or record[key] != value:
                matches = False
                break
        
        if matches:
            filtered_records.append(record)
    
    return filtered_records


def aggregate(records: List[Dict[str, Any]], field: str, agg: str) -> float:
    """
    Compute aggregation on a specified numeric field.
    
    Args:
        records: List of dictionaries to aggregate
        field: The field name to aggregate on
        agg: The aggregation type ('sum', 'avg', 'min', 'max')
        
    Returns:
        The aggregated value as a float
        
    Raises:
        TypeError: If records is not a list or contains non-dictionary items
        ValueError: If field is not found, agg is invalid, or no numeric values found
        KeyError: If field is not present in any record
        
    Examples:
        >>> records = [{'value': 10}, {'value': 20}, {'value': 30}]
        >>> aggregate(records, 'value', 'sum')
        60.0
        
        >>> aggregate(records, 'value', 'avg')
        20.0
    """
    if not isinstance(records, list):
        raise TypeError(f"Expected list, got {type(records).__name__}")
    
    if not isinstance(field, str):
        raise TypeError(f"Expected string field name, got {type(field).__name__}")
    
    if not isinstance(agg, str):
        raise TypeError(f"Expected string aggregation type, got {type(agg).__name__}")
    
    if not records:
        raise ValueError("Cannot aggregate empty list of records")
    
    # Validate aggregation type
    valid_aggs = {'sum', 'avg', 'min', 'max'}
    if agg.lower() not in valid_aggs:
        raise ValueError(f"Invalid aggregation type '{agg}'. Must be one of: {', '.join(valid_aggs)}")
    
    agg = agg.lower()
    
    # Validate that all items in records are dictionaries
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(f"Record at index {i} is not a dictionary, got {type(record).__name__}")
    
    # Extract values for the specified field
    values = []
    for i, record in enumerate(records):
        if field not in record:
            raise KeyError(f"Field '{field}' not found in record at index {i}")
        
        value = record[field]
        
        # Convert to numeric value
        try:
            if isinstance(value, (int, float)):
                numeric_value = float(value)
            elif isinstance(value, str):
                # Try to convert string to number
                numeric_value = float(value)
            elif isinstance(value, Decimal):
                numeric_value = float(value)
            else:
                raise ValueError(f"Non-numeric value '{value}' of type {type(value).__name__}")
            
            values.append(numeric_value)
            
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Non-numeric value '{value}' in field '{field}' at record {i}: {str(e)}")
    
    if not values:
        raise ValueError(f"No numeric values found in field '{field}'")
    
    # Perform aggregation
    if agg == 'sum':
        return sum(values)
    elif agg == 'avg':
        return sum(values) / len(values)
    elif agg == 'min':
        return min(values)
    elif agg == 'max':
        return max(values)
    
    # This should never be reached due to validation above
    raise ValueError(f"Unsupported aggregation type: {agg}")
