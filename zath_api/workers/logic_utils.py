"""
Logic utilities for data transformation operations.

This module provides looping and conditional logic functions that can be used
in data transformation workflows to apply complex business logic to records.
"""

import logging
from typing import Any, Callable, Dict, List, Union

logger = logging.getLogger(__name__)


def map_records(records: List[Any], func: Callable[[Any], Any]) -> List[Any]:
    """
    Apply a function to each item in a list of records.
    
    This function provides a functional programming approach to transforming
    collections of data by applying a transformation function to each element.
    
    Args:
        records: List of records to transform
        func: Function to apply to each record. Should accept a single argument
              and return a transformed version of that argument.
              
    Returns:
        List of transformed records
        
    Raises:
        TypeError: If records is not a list or func is not callable
        Exception: If the transformation function raises an exception
        
    Examples:
        >>> records = [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]
        >>> def add_prefix(record):
        ...     record["name"] = "Mr. " + record["name"]
        ...     return record
        >>> map_records(records, add_prefix)
        [{"name": "Mr. John", "age": 25}, {"name": "Mr. Jane", "age": 30}]
        
        >>> numbers = [1, 2, 3, 4, 5]
        >>> map_records(numbers, lambda x: x * 2)
        [2, 4, 6, 8, 10]
    """
    if not isinstance(records, list):
        raise TypeError(f"Expected records to be a list, got {type(records).__name__}")
    
    if not callable(func):
        raise TypeError(f"Expected func to be callable, got {type(func).__name__}")
    
    if not records:
        logger.info("Empty records list provided, returning empty list")
        return []
    
    try:
        result = []
        for i, record in enumerate(records):
            try:
                transformed_record = func(record)
                result.append(transformed_record)
            except Exception as e:
                logger.error(f"Error transforming record at index {i}: {e}")
                raise Exception(f"Error transforming record at index {i}: {e}")
        
        logger.info(f"Successfully transformed {len(result)} records")
        return result
        
    except Exception as e:
        logger.error(f"Error in map_records: {e}")
        raise


def conditional(
    record: Dict[str, Any], 
    condition: Callable[[Dict[str, Any]], bool], 
    if_func: Callable, 
    else_func: Callable
) -> Any:
    """
    Evaluate a condition on a record and apply different functions based on the result.
    
    This function provides conditional logic for data transformation, allowing
    different processing paths based on record content or properties.
    
    Args:
        record: Dictionary representing a single record
        condition: Function that takes a record and returns a boolean.
                   Determines which transformation to apply.
        if_func: Function to apply if condition returns True.
                 Should accept the record and return a transformed version.
        else_func: Function to apply if condition returns False.
                   Should accept the record and return a transformed version.
                   
    Returns:
        Result of applying either if_func or else_func to the record
        
    Raises:
        TypeError: If record is not a dict or any function is not callable
        Exception: If any of the functions raise an exception
        
    Examples:
        >>> record = {"age": 25, "name": "John"}
        >>> def is_adult(rec): return rec.get("age", 0) >= 18
        >>> def add_title(rec): 
        ...     rec["title"] = "Mr."
        ...     return rec
        >>> def add_minor_flag(rec):
        ...     rec["minor"] = True
        ...     return rec
        >>> conditional(record, is_adult, add_title, add_minor_flag)
        {"age": 25, "name": "John", "title": "Mr."}
        
        >>> record = {"age": 16, "name": "Jane"}
        >>> conditional(record, is_adult, add_title, add_minor_flag)
        {"age": 16, "name": "Jane", "minor": True}
    """
    if not isinstance(record, dict):
        raise TypeError(f"Expected record to be a dict, got {type(record).__name__}")
    
    if not callable(condition):
        raise TypeError(f"Expected condition to be callable, got {type(condition).__name__}")
    
    if not callable(if_func):
        raise TypeError(f"Expected if_func to be callable, got {type(if_func).__name__}")
    
    if not callable(else_func):
        raise TypeError(f"Expected else_func to be callable, got {type(else_func).__name__}")
    
    try:
        # Evaluate the condition
        condition_result = condition(record)
        
        if not isinstance(condition_result, bool):
            logger.warning(f"Condition function returned non-boolean value: {condition_result}")
            condition_result = bool(condition_result)
        
        # Apply the appropriate function
        if condition_result:
            logger.debug("Condition evaluated to True, applying if_func")
            result = if_func(record)
        else:
            logger.debug("Condition evaluated to False, applying else_func")
            result = else_func(record)
        
        logger.info(f"Conditional transformation completed, condition was {condition_result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in conditional transformation: {e}")
        raise Exception(f"Error in conditional transformation: {e}")


def create_condition_function(condition_spec: Dict[str, Any]) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a condition function from a specification dictionary.
    
    This helper function allows creating condition functions from JSON-serializable
    specifications, making it easier to define conditions in job payloads.
    
    Args:
        condition_spec: Dictionary specifying the condition logic.
                       Supported formats:
                       - {"field": "age", "operator": ">=", "value": 18}
                       - {"field": "status", "operator": "==", "value": "active"}
                       - {"field": "name", "operator": "contains", "value": "John"}
                       
    Returns:
        Callable condition function
        
    Raises:
        ValueError: If condition_spec is invalid
        KeyError: If required fields are missing
        
    Examples:
        >>> condition = create_condition_function({"field": "age", "operator": ">=", "value": 18})
        >>> condition({"age": 25})
        True
        >>> condition({"age": 16})
        False
    """
    if not isinstance(condition_spec, dict):
        raise ValueError("condition_spec must be a dictionary")
    
    required_fields = ["field", "operator", "value"]
    for field in required_fields:
        if field not in condition_spec:
            raise KeyError(f"Missing required field '{field}' in condition_spec")
    
    field = condition_spec["field"]
    operator = condition_spec["operator"]
    value = condition_spec["value"]
    
    def condition_func(record: Dict[str, Any]) -> bool:
        try:
            record_value = record.get(field)
            
            if operator == "==":
                return record_value == value
            elif operator == "!=":
                return record_value != value
            elif operator == ">":
                return record_value > value
            elif operator == ">=":
                return record_value >= value
            elif operator == "<":
                return record_value < value
            elif operator == "<=":
                return record_value <= value
            elif operator == "contains":
                return value in str(record_value) if record_value is not None else False
            elif operator == "not_contains":
                return value not in str(record_value) if record_value is not None else True
            elif operator == "in":
                return record_value in value if isinstance(value, (list, tuple, set)) else False
            elif operator == "not_in":
                return record_value not in value if isinstance(value, (list, tuple, set)) else True
            elif operator == "is_null":
                return record_value is None
            elif operator == "is_not_null":
                return record_value is not None
            else:
                raise ValueError(f"Unsupported operator: {operator}")
                
        except Exception as e:
            logger.error(f"Error evaluating condition {condition_spec}: {e}")
            return False
    
    return condition_func


def create_transform_function(transform_spec: Dict[str, Any]) -> Callable:
    """
    Create a transformation function from a specification dictionary.
    
    This helper function allows creating transformation functions from JSON-serializable
    specifications, making it easier to define transformations in job payloads.
    
    Args:
        transform_spec: Dictionary specifying the transformation logic.
                       Supported formats:
                       - {"type": "add_field", "field": "status", "value": "processed"}
                       - {"type": "update_field", "field": "name", "value": "Mr. {name}"}
                       - {"type": "remove_field", "field": "temp_data"}
                       
    Returns:
        Callable transformation function
        
    Raises:
        ValueError: If transform_spec is invalid
        KeyError: If required fields are missing
    """
    if not isinstance(transform_spec, dict):
        raise ValueError("transform_spec must be a dictionary")
    
    if "type" not in transform_spec:
        raise KeyError("Missing required field 'type' in transform_spec")
    
    transform_type = transform_spec["type"]
    
    def transform_func(record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Create a copy to avoid modifying the original
            result = record.copy()
            
            if transform_type == "add_field":
                if "field" not in transform_spec or "value" not in transform_spec:
                    raise KeyError("add_field requires 'field' and 'value'")
                result[transform_spec["field"]] = transform_spec["value"]
                
            elif transform_type == "update_field":
                if "field" not in transform_spec or "value" not in transform_spec:
                    raise KeyError("update_field requires 'field' and 'value'")
                field = transform_spec["field"]
                value_template = transform_spec["value"]
                # Simple string formatting with record values
                if isinstance(value_template, str) and "{" in value_template:
                    result[field] = value_template.format(**result)
                else:
                    result[field] = value_template
                    
            elif transform_type == "remove_field":
                if "field" not in transform_spec:
                    raise KeyError("remove_field requires 'field'")
                result.pop(transform_spec["field"], None)
                
            elif transform_type == "multiply_field":
                if "field" not in transform_spec or "value" not in transform_spec:
                    raise KeyError("multiply_field requires 'field' and 'value'")
                field = transform_spec["field"]
                if field in result and isinstance(result[field], (int, float)):
                    result[field] = result[field] * transform_spec["value"]
                    
            elif transform_type == "add_to_field":
                if "field" not in transform_spec or "value" not in transform_spec:
                    raise KeyError("add_to_field requires 'field' and 'value'")
                field = transform_spec["field"]
                if field in result and isinstance(result[field], (int, float)):
                    result[field] = result[field] + transform_spec["value"]
                    
            else:
                raise ValueError(f"Unsupported transform type: {transform_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in transform function {transform_spec}: {e}")
            raise Exception(f"Error in transform function: {e}")
    
    return transform_func
