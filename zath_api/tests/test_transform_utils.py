"""
Unit tests for transform_utils module.

This module tests all functions in transform_utils.py with comprehensive
coverage of typical cases, edge cases, and error conditions.
"""

import pytest
from decimal import Decimal
from transform_utils import flatten_json, csv_to_json, filter_records, aggregate


class TestFlattenJson:
    """Test cases for flatten_json function."""
    
    def test_simple_flatten(self):
        """Test flattening a simple nested dictionary."""
        data = {'a': {'b': 1, 'c': 2}}
        result = flatten_json(data)
        expected = {'a.b': 1, 'a.c': 2}
        assert result == expected
    
    def test_deeply_nested(self):
        """Test flattening deeply nested dictionaries."""
        data = {'a': {'b': {'c': {'d': 42}}}}
        result = flatten_json(data)
        expected = {'a.b.c.d': 42}
        assert result == expected
    
    def test_multiple_nested_keys(self):
        """Test flattening with multiple nested keys."""
        data = {
            'user': {'name': 'John', 'age': 30},
            'address': {'city': 'NYC', 'zip': '10001'}
        }
        result = flatten_json(data)
        expected = {
            'user.name': 'John',
            'user.age': 30,
            'address.city': 'NYC',
            'address.zip': '10001'
        }
        assert result == expected
    
    def test_with_lists(self):
        """Test flattening with list values."""
        data = {'items': [1, 2, 3], 'nested': {'list': ['a', 'b']}}
        result = flatten_json(data)
        expected = {'items': [1, 2, 3], 'nested.list': ['a', 'b']}
        assert result == expected
    
    def test_custom_separator(self):
        """Test flattening with custom separator."""
        data = {'a': {'b': 1}}
        result = flatten_json(data, sep='_')
        expected = {'a_b': 1}
        assert result == expected
    
    def test_empty_dict(self):
        """Test flattening empty dictionary."""
        data = {}
        result = flatten_json(data)
        expected = {}
        assert result == expected
    
    def test_primitive_values(self):
        """Test flattening with primitive values."""
        data = {'string': 'hello', 'number': 42, 'boolean': True, 'none': None}
        result = flatten_json(data)
        expected = {'string': 'hello', 'number': 42, 'boolean': True, 'none': None}
        assert result == expected
    
    def test_non_dict_input(self):
        """Test error handling for non-dictionary input."""
        with pytest.raises(TypeError, match="Expected dict, got"):
            flatten_json("not a dict")
        
        with pytest.raises(TypeError, match="Expected dict, got"):
            flatten_json([1, 2, 3])
        
        with pytest.raises(TypeError, match="Expected dict, got"):
            flatten_json(42)
    
    def test_non_string_keys(self):
        """Test error handling for non-string dictionary keys."""
        data = {1: 'value', 2: 'another'}
        with pytest.raises(ValueError, match="Dictionary keys must be strings"):
            flatten_json(data)


class TestCsvToJson:
    """Test cases for csv_to_json function."""
    
    def test_basic_csv(self):
        """Test basic CSV parsing."""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        result = csv_to_json(csv_content)
        expected = [
            {'name': 'John', 'age': '25', 'city': 'NYC'},
            {'name': 'Jane', 'age': '30', 'city': 'LA'}
        ]
        assert result == expected
    
    def test_custom_delimiter(self):
        """Test CSV parsing with custom delimiter."""
        csv_content = "name;age;city\nJohn;25;NYC\nJane;30;LA"
        result = csv_to_json(csv_content, delimiter=';')
        expected = [
            {'name': 'John', 'age': '25', 'city': 'NYC'},
            {'name': 'Jane', 'age': '30', 'city': 'LA'}
        ]
        assert result == expected
    
    def test_single_row(self):
        """Test CSV with single data row."""
        csv_content = "name,age\nJohn,25"
        result = csv_to_json(csv_content)
        expected = [{'name': 'John', 'age': '25'}]
        assert result == expected
    
    def test_empty_values(self):
        """Test CSV with empty values."""
        csv_content = "name,age,city\nJohn,,NYC\n,30,LA"
        result = csv_to_json(csv_content)
        expected = [
            {'name': 'John', 'age': '', 'city': 'NYC'},
            {'name': '', 'age': '30', 'city': 'LA'}
        ]
        assert result == expected
    
    def test_quoted_values(self):
        """Test CSV with quoted values."""
        csv_content = 'name,description\nJohn,"A person, with comma"\nJane,"Another person"'
        result = csv_to_json(csv_content)
        expected = [
            {'name': 'John', 'description': 'A person, with comma'},
            {'name': 'Jane', 'description': 'Another person'}
        ]
        assert result == expected
    
    def test_tab_delimiter(self):
        """Test CSV with tab delimiter."""
        csv_content = "name\tage\nJohn\t25\nJane\t30"
        result = csv_to_json(csv_content, delimiter='\t')
        expected = [
            {'name': 'John', 'age': '25'},
            {'name': 'Jane', 'age': '30'}
        ]
        assert result == expected
    
    def test_non_string_input(self):
        """Test error handling for non-string input."""
        with pytest.raises(TypeError, match="Expected string, got"):
            csv_to_json(123)
        
        with pytest.raises(TypeError, match="Expected string, got"):
            csv_to_json(['a', 'b', 'c'])
    
    def test_non_string_delimiter(self):
        """Test error handling for non-string delimiter."""
        with pytest.raises(TypeError, match="Expected string delimiter, got"):
            csv_to_json("a,b\n1,2", delimiter=123)
    
    def test_empty_content(self):
        """Test error handling for empty content."""
        with pytest.raises(ValueError, match="CSV content cannot be empty"):
            csv_to_json("")
        
        with pytest.raises(ValueError, match="CSV content cannot be empty"):
            csv_to_json("   ")
    
    def test_invalid_delimiter(self):
        """Test error handling for invalid delimiter."""
        with pytest.raises(ValueError, match="Delimiter must be a single character"):
            csv_to_json("a,b\n1,2", delimiter="")
        
        with pytest.raises(ValueError, match="Delimiter must be a single character"):
            csv_to_json("a,b\n1,2", delimiter="ab")
    
    def test_no_data_rows(self):
        """Test error handling for CSV with only headers."""
        csv_content = "name,age"
        with pytest.raises(ValueError, match="CSV content contains no data rows"):
            csv_to_json(csv_content)
    
    def test_malformed_csv(self):
        """Test error handling for malformed CSV."""
        csv_content = "name,age\nJohn,25\nJane"  # Missing value
        # CSV parser is lenient and will handle missing values as None
        result = csv_to_json(csv_content)
        expected = [
            {'name': 'John', 'age': '25'},
            {'name': 'Jane', 'age': None}
        ]
        assert result == expected


class TestFilterRecords:
    """Test cases for filter_records function."""
    
    def test_single_criterion(self):
        """Test filtering with single criterion."""
        records = [
            {'name': 'John', 'age': 25, 'city': 'NYC'},
            {'name': 'Jane', 'age': 30, 'city': 'LA'},
            {'name': 'Bob', 'age': 25, 'city': 'Chicago'}
        ]
        result = filter_records(records, age=25)
        expected = [
            {'name': 'John', 'age': 25, 'city': 'NYC'},
            {'name': 'Bob', 'age': 25, 'city': 'Chicago'}
        ]
        assert result == expected
    
    def test_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        records = [
            {'name': 'John', 'age': 25, 'city': 'NYC'},
            {'name': 'Jane', 'age': 30, 'city': 'LA'},
            {'name': 'John', 'age': 30, 'city': 'NYC'}
        ]
        result = filter_records(records, name='John', city='NYC')
        expected = [
            {'name': 'John', 'age': 25, 'city': 'NYC'},
            {'name': 'John', 'age': 30, 'city': 'NYC'}
        ]
        assert result == expected
    
    def test_no_matches(self):
        """Test filtering with no matching records."""
        records = [
            {'name': 'John', 'age': 25},
            {'name': 'Jane', 'age': 30}
        ]
        result = filter_records(records, age=40)
        expected = []
        assert result == expected
    
    def test_empty_records(self):
        """Test filtering empty record list."""
        records = []
        result = filter_records(records, age=25)
        expected = []
        assert result == expected
    
    def test_string_values(self):
        """Test filtering with string values."""
        records = [
            {'status': 'active', 'type': 'user'},
            {'status': 'inactive', 'type': 'admin'},
            {'status': 'active', 'type': 'admin'}
        ]
        result = filter_records(records, status='active')
        expected = [
            {'status': 'active', 'type': 'user'},
            {'status': 'active', 'type': 'admin'}
        ]
        assert result == expected
    
    def test_boolean_values(self):
        """Test filtering with boolean values."""
        records = [
            {'active': True, 'verified': False},
            {'active': False, 'verified': True},
            {'active': True, 'verified': True}
        ]
        result = filter_records(records, active=True)
        expected = [
            {'active': True, 'verified': False},
            {'active': True, 'verified': True}
        ]
        assert result == expected
    
    def test_none_values(self):
        """Test filtering with None values."""
        records = [
            {'name': 'John', 'age': 25},
            {'name': None, 'age': 30},
            {'name': 'Jane', 'age': None}
        ]
        result = filter_records(records, name=None)
        expected = [{'name': None, 'age': 30}]
        assert result == expected
    
    def test_non_list_input(self):
        """Test error handling for non-list input."""
        with pytest.raises(TypeError, match="Expected list, got"):
            filter_records("not a list", age=25)
        
        with pytest.raises(TypeError, match="Expected list, got"):
            filter_records({'a': 1}, age=25)
    
    def test_non_dict_records(self):
        """Test error handling for non-dictionary records."""
        records = [{'name': 'John'}, "not a dict", {'name': 'Jane'}]
        with pytest.raises(TypeError, match="Record at index 1 is not a dictionary"):
            filter_records(records, name='John')
    
    def test_empty_criteria(self):
        """Test error handling for empty criteria."""
        records = [{'name': 'John'}]
        with pytest.raises(ValueError, match="At least one filter criterion must be provided"):
            filter_records(records)


class TestAggregate:
    """Test cases for aggregate function."""
    
    def test_sum_aggregation(self):
        """Test sum aggregation."""
        records = [{'value': 10}, {'value': 20}, {'value': 30}]
        result = aggregate(records, 'value', 'sum')
        assert result == 60.0
    
    def test_avg_aggregation(self):
        """Test average aggregation."""
        records = [{'value': 10}, {'value': 20}, {'value': 30}]
        result = aggregate(records, 'value', 'avg')
        assert result == 20.0
    
    def test_min_aggregation(self):
        """Test minimum aggregation."""
        records = [{'value': 30}, {'value': 10}, {'value': 20}]
        result = aggregate(records, 'value', 'min')
        assert result == 10.0
    
    def test_max_aggregation(self):
        """Test maximum aggregation."""
        records = [{'value': 10}, {'value': 30}, {'value': 20}]
        result = aggregate(records, 'value', 'max')
        assert result == 30.0
    
    def test_case_insensitive_agg(self):
        """Test case-insensitive aggregation type."""
        records = [{'value': 10}, {'value': 20}]
        result = aggregate(records, 'value', 'SUM')
        assert result == 30.0
        
        result = aggregate(records, 'value', 'AVG')
        assert result == 15.0
    
    def test_string_numbers(self):
        """Test aggregation with string numbers."""
        records = [{'value': '10'}, {'value': '20'}, {'value': '30'}]
        result = aggregate(records, 'value', 'sum')
        assert result == 60.0
    
    def test_mixed_numeric_types(self):
        """Test aggregation with mixed numeric types."""
        records = [
            {'value': 10},
            {'value': 20.5},
            {'value': '30'},
            {'value': Decimal('40.5')}
        ]
        result = aggregate(records, 'value', 'sum')
        assert result == 101.0
    
    def test_float_precision(self):
        """Test aggregation with float precision."""
        records = [{'value': 0.1}, {'value': 0.2}]
        result = aggregate(records, 'value', 'sum')
        assert abs(result - 0.3) < 1e-10  # Account for floating point precision
    
    def test_single_record(self):
        """Test aggregation with single record."""
        records = [{'value': 42}]
        result = aggregate(records, 'value', 'sum')
        assert result == 42.0
        
        result = aggregate(records, 'value', 'avg')
        assert result == 42.0
    
    def test_negative_numbers(self):
        """Test aggregation with negative numbers."""
        records = [{'value': -10}, {'value': 20}, {'value': -5}]
        result = aggregate(records, 'value', 'sum')
        assert result == 5.0
        
        result = aggregate(records, 'value', 'min')
        assert result == -10.0
    
    def test_zero_values(self):
        """Test aggregation with zero values."""
        records = [{'value': 0}, {'value': 10}, {'value': 0}]
        result = aggregate(records, 'value', 'sum')
        assert result == 10.0
        
        result = aggregate(records, 'value', 'avg')
        assert result == 10.0 / 3
    
    def test_non_list_input(self):
        """Test error handling for non-list input."""
        with pytest.raises(TypeError, match="Expected list, got"):
            aggregate("not a list", 'value', 'sum')
        
        with pytest.raises(TypeError, match="Expected list, got"):
            aggregate({'a': 1}, 'value', 'sum')
    
    def test_non_string_field(self):
        """Test error handling for non-string field."""
        records = [{'value': 10}]
        with pytest.raises(TypeError, match="Expected string field name, got"):
            aggregate(records, 123, 'sum')
    
    def test_non_string_agg(self):
        """Test error handling for non-string aggregation type."""
        records = [{'value': 10}]
        with pytest.raises(TypeError, match="Expected string aggregation type, got"):
            aggregate(records, 'value', 123)
    
    def test_empty_records(self):
        """Test error handling for empty records."""
        records = []
        with pytest.raises(ValueError, match="Cannot aggregate empty list of records"):
            aggregate(records, 'value', 'sum')
    
    def test_invalid_aggregation_type(self):
        """Test error handling for invalid aggregation type."""
        records = [{'value': 10}]
        with pytest.raises(ValueError, match="Invalid aggregation type 'invalid'"):
            aggregate(records, 'value', 'invalid')
    
    def test_non_dict_records(self):
        """Test error handling for non-dictionary records."""
        records = [{'value': 10}, "not a dict"]
        with pytest.raises(TypeError, match="Record at index 1 is not a dictionary"):
            aggregate(records, 'value', 'sum')
    
    def test_missing_field(self):
        """Test error handling for missing field."""
        records = [{'value': 10}, {'other': 20}]
        with pytest.raises(KeyError, match="Field 'value' not found in record at index 1"):
            aggregate(records, 'value', 'sum')
    
    def test_non_numeric_values(self):
        """Test error handling for non-numeric values."""
        records = [{'value': 10}, {'value': 'not a number'}]
        with pytest.raises(ValueError, match="Non-numeric value 'not a number'"):
            aggregate(records, 'value', 'sum')
        
        records = [{'value': 10}, {'value': [1, 2, 3]}]
        with pytest.raises(ValueError, match="Non-numeric value"):
            aggregate(records, 'value', 'sum')
    
    def test_all_non_numeric_values(self):
        """Test error handling when all values are non-numeric."""
        records = [{'value': 'not a number'}, {'value': 'also not a number'}]
        with pytest.raises(ValueError, match="Non-numeric value 'not a number'"):
            aggregate(records, 'value', 'sum')


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_csv_filter_aggregate_workflow(self):
        """Test a complete workflow: CSV -> filter -> aggregate."""
        csv_content = "name,age,salary\nJohn,25,50000\nJane,30,60000\nBob,25,45000"
        
        # Parse CSV
        records = csv_to_json(csv_content)
        
        # Filter by age
        filtered = filter_records(records, age='25')
        
        # Convert salary to numeric and aggregate
        numeric_records = [{'salary': float(r['salary'])} for r in filtered]
        total_salary = aggregate(numeric_records, 'salary', 'sum')
        
        assert total_salary == 95000.0
    
    def test_flatten_filter_workflow(self):
        """Test a workflow: flatten JSON -> filter."""
        nested_data = {
            'users': [
                {'name': 'John', 'details': {'age': 25, 'active': True}},
                {'name': 'Jane', 'details': {'age': 30, 'active': False}}
            ]
        }
        
        # Flatten the structure
        flattened = flatten_json(nested_data)
        
        # This would be a more complex workflow in practice
        assert 'users' in flattened
        assert isinstance(flattened['users'], list)
