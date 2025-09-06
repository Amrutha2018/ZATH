"""
Unit tests for logic_utils module.

Tests the looping and conditional logic utilities including map_records,
conditional, and helper functions for creating condition and transform functions.
"""

import pytest
from logic_utils import (
    map_records,
    conditional,
    create_condition_function,
    create_transform_function
)


class TestMapRecords:
    """Test cases for map_records function."""
    
    def test_basic_mapping(self):
        """Test basic mapping functionality."""
        records = [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]
        
        def add_prefix(record):
            record["name"] = "Mr. " + record["name"]
            return record
        
        result = map_records(records, add_prefix)
        
        assert len(result) == 2
        assert result[0]["name"] == "Mr. John"
        assert result[1]["name"] == "Mr. Jane"
        assert result[0]["age"] == 25
        assert result[1]["age"] == 30
    
    def test_numeric_mapping(self):
        """Test mapping with numeric data."""
        numbers = [1, 2, 3, 4, 5]
        
        result = map_records(numbers, lambda x: x * 2)
        
        assert result == [2, 4, 6, 8, 10]
    
    def test_empty_list(self):
        """Test mapping with empty list."""
        result = map_records([], lambda x: x)
        assert result == []
    
    def test_single_record(self):
        """Test mapping with single record."""
        records = [{"value": 10}]
        
        def double_value(record):
            record["value"] = record["value"] * 2
            return record
        
        result = map_records(records, double_value)
        
        assert len(result) == 1
        assert result[0]["value"] == 20
    
    def test_non_dict_records(self):
        """Test mapping with non-dictionary records."""
        records = ["hello", "world", "test"]
        
        def uppercase_string(s):
            return s.upper()
        
        result = map_records(records, uppercase_string)
        
        assert result == ["HELLO", "WORLD", "TEST"]
    
    def test_invalid_input_type(self):
        """Test map_records with invalid input type."""
        with pytest.raises(TypeError, match="Expected records to be a list"):
            map_records("not a list", lambda x: x)
    
    def test_invalid_function_type(self):
        """Test map_records with invalid function type."""
        with pytest.raises(TypeError, match="Expected func to be callable"):
            map_records([1, 2, 3], "not a function")
    
    def test_function_raises_exception(self):
        """Test map_records when function raises exception."""
        records = [{"value": 10}, {"value": "invalid"}]
        
        def divide_by_two(record):
            return record["value"] / 2
        
        with pytest.raises(Exception, match="Error transforming record at index 1"):
            map_records(records, divide_by_two)


class TestConditional:
    """Test cases for conditional function."""
    
    def test_condition_true(self):
        """Test conditional when condition is true."""
        record = {"age": 25, "name": "John"}
        
        def is_adult(rec):
            return rec.get("age", 0) >= 18
        
        def add_title(rec):
            rec["title"] = "Mr."
            return rec
        
        def add_minor_flag(rec):
            rec["minor"] = True
            return rec
        
        result = conditional(record, is_adult, add_title, add_minor_flag)
        
        assert result["age"] == 25
        assert result["name"] == "John"
        assert result["title"] == "Mr."
        assert "minor" not in result
    
    def test_condition_false(self):
        """Test conditional when condition is false."""
        record = {"age": 16, "name": "Jane"}
        
        def is_adult(rec):
            return rec.get("age", 0) >= 18
        
        def add_title(rec):
            rec["title"] = "Mr."
            return rec
        
        def add_minor_flag(rec):
            rec["minor"] = True
            return rec
        
        result = conditional(record, is_adult, add_title, add_minor_flag)
        
        assert result["age"] == 16
        assert result["name"] == "Jane"
        assert result["minor"] is True
        assert "title" not in result
    
    def test_condition_with_string_comparison(self):
        """Test conditional with string comparison."""
        record = {"status": "active", "name": "User1"}
        
        def is_active(rec):
            return rec.get("status") == "active"
        
        def mark_processed(rec):
            rec["processed"] = True
            return rec
        
        def mark_pending(rec):
            rec["pending"] = True
            return rec
        
        result = conditional(record, is_active, mark_processed, mark_pending)
        
        assert result["processed"] is True
        assert "pending" not in result
    
    def test_condition_always_false(self):
        """Test conditional with condition that's always false."""
        record = {"value": 5}
        
        def always_false(rec):
            return False
        
        def if_func(rec):
            rec["if_applied"] = True
            return rec
        
        def else_func(rec):
            rec["else_applied"] = True
            return rec
        
        result = conditional(record, always_false, if_func, else_func)
        
        assert result["else_applied"] is True
        assert "if_applied" not in result
    
    def test_condition_always_true(self):
        """Test conditional with condition that's always true."""
        record = {"value": 5}
        
        def always_true(rec):
            return True
        
        def if_func(rec):
            rec["if_applied"] = True
            return rec
        
        def else_func(rec):
            rec["else_applied"] = True
            return rec
        
        result = conditional(record, always_true, if_func, else_func)
        
        assert result["if_applied"] is True
        assert "else_applied" not in result
    
    def test_non_boolean_condition_result(self):
        """Test conditional with non-boolean condition result."""
        record = {"value": 5}
        
        def return_number(rec):
            return 1  # Non-boolean truthy value
        
        def if_func(rec):
            rec["if_applied"] = True
            return rec
        
        def else_func(rec):
            rec["else_applied"] = True
            return rec
        
        result = conditional(record, return_number, if_func, else_func)
        
        assert result["if_applied"] is True
        assert "else_applied" not in result
    
    def test_invalid_record_type(self):
        """Test conditional with invalid record type."""
        with pytest.raises(TypeError, match="Expected record to be a dict"):
            conditional("not a dict", lambda x: True, lambda x: x, lambda x: x)
    
    def test_invalid_condition_type(self):
        """Test conditional with invalid condition type."""
        with pytest.raises(TypeError, match="Expected condition to be callable"):
            conditional({"test": "data"}, "not callable", lambda x: x, lambda x: x)
    
    def test_invalid_if_func_type(self):
        """Test conditional with invalid if_func type."""
        with pytest.raises(TypeError, match="Expected if_func to be callable"):
            conditional({"test": "data"}, lambda x: True, "not callable", lambda x: x)
    
    def test_invalid_else_func_type(self):
        """Test conditional with invalid else_func type."""
        with pytest.raises(TypeError, match="Expected else_func to be callable"):
            conditional({"test": "data"}, lambda x: True, lambda x: x, "not callable")
    
    def test_condition_raises_exception(self):
        """Test conditional when condition raises exception."""
        record = {"value": 5}
        
        def failing_condition(rec):
            raise ValueError("Condition failed")
        
        def if_func(rec):
            return rec
        
        def else_func(rec):
            return rec
        
        with pytest.raises(Exception, match="Error in conditional transformation"):
            conditional(record, failing_condition, if_func, else_func)


class TestCreateConditionFunction:
    """Test cases for create_condition_function."""
    
    def test_equals_operator(self):
        """Test condition function with equals operator."""
        condition = create_condition_function({"field": "age", "operator": "==", "value": 25})
        
        assert condition({"age": 25}) is True
        assert condition({"age": 30}) is False
        assert condition({"age": "25"}) is False
    
    def test_not_equals_operator(self):
        """Test condition function with not equals operator."""
        condition = create_condition_function({"field": "status", "operator": "!=", "value": "inactive"})
        
        assert condition({"status": "active"}) is True
        assert condition({"status": "inactive"}) is False
    
    def test_greater_than_operator(self):
        """Test condition function with greater than operator."""
        condition = create_condition_function({"field": "score", "operator": ">", "value": 80})
        
        assert condition({"score": 85}) is True
        assert condition({"score": 80}) is False
        assert condition({"score": 75}) is False
    
    def test_greater_than_or_equal_operator(self):
        """Test condition function with greater than or equal operator."""
        condition = create_condition_function({"field": "age", "operator": ">=", "value": 18})
        
        assert condition({"age": 18}) is True
        assert condition({"age": 25}) is True
        assert condition({"age": 16}) is False
    
    def test_less_than_operator(self):
        """Test condition function with less than operator."""
        condition = create_condition_function({"field": "price", "operator": "<", "value": 100})
        
        assert condition({"price": 50}) is True
        assert condition({"price": 100}) is False
        assert condition({"price": 150}) is False
    
    def test_less_than_or_equal_operator(self):
        """Test condition function with less than or equal operator."""
        condition = create_condition_function({"field": "quantity", "operator": "<=", "value": 10})
        
        assert condition({"quantity": 10}) is True
        assert condition({"quantity": 5}) is True
        assert condition({"quantity": 15}) is False
    
    def test_contains_operator(self):
        """Test condition function with contains operator."""
        condition = create_condition_function({"field": "name", "operator": "contains", "value": "John"})
        
        assert condition({"name": "John Doe"}) is True
        assert condition({"name": "Jane Smith"}) is False
        assert condition({"name": "johnny"}) is False  # Case sensitive, "John" not in "johnny"
    
    def test_not_contains_operator(self):
        """Test condition function with not contains operator."""
        condition = create_condition_function({"field": "description", "operator": "not_contains", "value": "error"})
        
        assert condition({"description": "success message"}) is True
        assert condition({"description": "error occurred"}) is False
    
    def test_in_operator(self):
        """Test condition function with in operator."""
        condition = create_condition_function({"field": "status", "operator": "in", "value": ["active", "pending"]})
        
        assert condition({"status": "active"}) is True
        assert condition({"status": "pending"}) is True
        assert condition({"status": "inactive"}) is False
    
    def test_not_in_operator(self):
        """Test condition function with not in operator."""
        condition = create_condition_function({"field": "category", "operator": "not_in", "value": ["deleted", "archived"]})
        
        assert condition({"category": "active"}) is True
        assert condition({"category": "deleted"}) is False
    
    def test_is_null_operator(self):
        """Test condition function with is null operator."""
        condition = create_condition_function({"field": "optional_field", "operator": "is_null", "value": None})
        
        assert condition({"optional_field": None}) is True
        assert condition({"optional_field": "value"}) is False
        assert condition({}) is True  # Missing field is considered null
    
    def test_is_not_null_operator(self):
        """Test condition function with is not null operator."""
        condition = create_condition_function({"field": "required_field", "operator": "is_not_null", "value": None})
        
        assert condition({"required_field": "value"}) is True
        assert condition({"required_field": None}) is False
        assert condition({}) is False  # Missing field is considered null
    
    def test_missing_field(self):
        """Test condition function with missing field."""
        condition = create_condition_function({"field": "missing_field", "operator": "==", "value": "test"})
        
        assert condition({}) is False
        assert condition({"other_field": "value"}) is False
    
    def test_invalid_operator(self):
        """Test condition function with invalid operator."""
        # The function creates successfully but returns False when evaluated
        condition = create_condition_function({"field": "test", "operator": "invalid", "value": "test"})
        assert condition({"test": "data"}) is False
    
    def test_missing_required_fields(self):
        """Test condition function with missing required fields."""
        with pytest.raises(KeyError, match="Missing required field"):
            create_condition_function({"field": "test"})  # Missing operator and value
    
    def test_invalid_condition_spec_type(self):
        """Test condition function with invalid condition spec type."""
        with pytest.raises(ValueError, match="condition_spec must be a dictionary"):
            create_condition_function("not a dict")


class TestCreateTransformFunction:
    """Test cases for create_transform_function."""
    
    def test_add_field_transform(self):
        """Test add field transformation."""
        transform = create_transform_function({"type": "add_field", "field": "status", "value": "processed"})
        
        record = {"name": "John", "age": 25}
        result = transform(record)
        
        assert result["name"] == "John"
        assert result["age"] == 25
        assert result["status"] == "processed"
    
    def test_update_field_transform(self):
        """Test update field transformation."""
        transform = create_transform_function({"type": "update_field", "field": "name", "value": "Mr. {name}"})
        
        record = {"name": "John", "age": 25}
        result = transform(record)
        
        assert result["name"] == "Mr. John"
        assert result["age"] == 25
    
    def test_remove_field_transform(self):
        """Test remove field transformation."""
        transform = create_transform_function({"type": "remove_field", "field": "temp_data"})
        
        record = {"name": "John", "temp_data": "temporary", "age": 25}
        result = transform(record)
        
        assert result["name"] == "John"
        assert result["age"] == 25
        assert "temp_data" not in result
    
    def test_multiply_field_transform(self):
        """Test multiply field transformation."""
        transform = create_transform_function({"type": "multiply_field", "field": "price", "value": 1.1})
        
        record = {"name": "Product", "price": 100}
        result = transform(record)
        
        assert result["name"] == "Product"
        assert abs(result["price"] - 110.0) < 0.0001  # Handle floating point precision
    
    def test_add_to_field_transform(self):
        """Test add to field transformation."""
        transform = create_transform_function({"type": "add_to_field", "field": "quantity", "value": 5})
        
        record = {"name": "Item", "quantity": 10}
        result = transform(record)
        
        assert result["name"] == "Item"
        assert result["quantity"] == 15
    
    def test_multiply_field_with_non_numeric(self):
        """Test multiply field with non-numeric value."""
        transform = create_transform_function({"type": "multiply_field", "field": "name", "value": 2})
        
        record = {"name": "John", "age": 25}
        result = transform(record)
        
        # Non-numeric field should remain unchanged
        assert result["name"] == "John"
        assert result["age"] == 25
    
    def test_add_to_field_with_non_numeric(self):
        """Test add to field with non-numeric value."""
        transform = create_transform_function({"type": "add_to_field", "field": "name", "value": 5})
        
        record = {"name": "John", "age": 25}
        result = transform(record)
        
        # Non-numeric field should remain unchanged
        assert result["name"] == "John"
        assert result["age"] == 25
    
    def test_remove_nonexistent_field(self):
        """Test remove field that doesn't exist."""
        transform = create_transform_function({"type": "remove_field", "field": "nonexistent"})
        
        record = {"name": "John", "age": 25}
        result = transform(record)
        
        assert result["name"] == "John"
        assert result["age"] == 25
    
    def test_invalid_transform_type(self):
        """Test transform function with invalid type."""
        transform = create_transform_function({"type": "invalid_type", "field": "test"})
        with pytest.raises(Exception, match="Error in transform function"):
            transform({"test": "data"})
    
    def test_missing_required_fields(self):
        """Test transform function with missing required fields."""
        transform = create_transform_function({"type": "add_field", "field": "test"})  # Missing value
        with pytest.raises(Exception, match="Error in transform function"):
            transform({"test": "data"})
    
    def test_invalid_transform_spec_type(self):
        """Test transform function with invalid spec type."""
        with pytest.raises(ValueError, match="transform_spec must be a dictionary"):
            create_transform_function("not a dict")
    
    def test_missing_type_field(self):
        """Test transform function with missing type field."""
        with pytest.raises(KeyError, match="Missing required field 'type'"):
            create_transform_function({"field": "test", "value": "test"})


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_map_with_conditional_logic(self):
        """Test combining map_records with conditional logic."""
        records = [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 16},
            {"name": "Bob", "age": 30}
        ]
        
        def process_record(record):
            def is_adult(rec):
                return rec.get("age", 0) >= 18
            
            def add_title(rec):
                rec["title"] = "Mr."
                return rec
            
            def add_minor_flag(rec):
                rec["minor"] = True
                return rec
            
            return conditional(record, is_adult, add_title, add_minor_flag)
        
        result = map_records(records, process_record)
        
        assert len(result) == 3
        assert result[0]["title"] == "Mr."
        assert "minor" not in result[0]
        assert result[1]["minor"] is True
        assert "title" not in result[1]
        assert result[2]["title"] == "Mr."
        assert "minor" not in result[2]
    
    def test_conditional_with_created_functions(self):
        """Test conditional with created condition and transform functions."""
        record = {"age": 25, "name": "John"}
        
        condition = create_condition_function({"field": "age", "operator": ">=", "value": 18})
        if_func = create_transform_function({"type": "add_field", "field": "category", "value": "adult"})
        else_func = create_transform_function({"type": "add_field", "field": "category", "value": "minor"})
        
        result = conditional(record, condition, if_func, else_func)
        
        assert result["age"] == 25
        assert result["name"] == "John"
        assert result["category"] == "adult"
    
    def test_complex_transformation_workflow(self):
        """Test a complex transformation workflow."""
        records = [
            {"name": "John", "age": 25, "salary": 50000},
            {"name": "Jane", "age": 16, "salary": 0},
            {"name": "Bob", "age": 30, "salary": 75000}
        ]
        
        # Step 1: Add tax calculation for adults
        def add_tax(record):
            def is_adult(rec):
                return rec.get("age", 0) >= 18
            
            def calculate_tax(rec):
                rec["tax"] = rec.get("salary", 0) * 0.2
                return rec
            
            def no_tax(rec):
                rec["tax"] = 0
                return rec
            
            return conditional(record, is_adult, calculate_tax, no_tax)
        
        # Step 2: Add status based on salary
        def add_status(record):
            def has_salary(rec):
                return rec.get("salary", 0) > 0
            
            def employed(rec):
                rec["status"] = "employed"
                return rec
            
            def unemployed(rec):
                rec["status"] = "unemployed"
                return rec
            
            return conditional(record, has_salary, employed, unemployed)
        
        # Apply transformations
        step1_result = map_records(records, add_tax)
        step2_result = map_records(step1_result, add_status)
        
        assert len(step2_result) == 3
        
        # Check John (adult, employed)
        assert step2_result[0]["tax"] == 10000
        assert step2_result[0]["status"] == "employed"
        
        # Check Jane (minor, unemployed)
        assert step2_result[1]["tax"] == 0
        assert step2_result[1]["status"] == "unemployed"
        
        # Check Bob (adult, employed)
        assert step2_result[2]["tax"] == 15000
        assert step2_result[2]["status"] == "employed"
