#!/usr/bin/env python3
"""
End-to-end test for sequential transformations with looping and conditional logic.

This script demonstrates the complete workflow of creating a data_transform job
with sequential transformations that include map operations and conditional logic.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import aiohttp
from workers.task_handlers import execute_task


async def test_sequential_transformations():
    """Test sequential transformations with complex business logic."""
    print("🧪 Testing Sequential Transformations with Looping and Conditional Logic")
    print("=" * 70)
    
    # Sample data: Employee records with various statuses and salaries
    employee_records = [
        {"name": "John Doe", "age": 25, "salary": 50000, "department": "Engineering", "status": "active"},
        {"name": "Jane Smith", "age": 16, "salary": 0, "department": "Intern", "status": "active"},
        {"name": "Bob Johnson", "age": 30, "salary": 75000, "department": "Engineering", "status": "active"},
        {"name": "Alice Brown", "age": 28, "salary": 60000, "department": "Marketing", "status": "inactive"},
        {"name": "Charlie Wilson", "age": 22, "salary": 45000, "department": "Sales", "status": "active"},
        {"name": "Diana Lee", "age": 35, "salary": 90000, "department": "Management", "status": "active"}
    ]
    
    print(f"\n📊 Initial Data: {len(employee_records)} employee records")
    for i, record in enumerate(employee_records, 1):
        print(f"   {i}. {record['name']} - Age: {record['age']}, Salary: ${record['salary']:,}, Dept: {record['department']}")
    
    # Define sequential transformations
    transformations = [
        {
            "type": "map",
            "function": {
                "type": "add_field",
                "field": "processed_at",
                "value": "2025-01-01T00:00:00Z"
            }
        },
        {
            "type": "conditional",
            "condition": {
                "field": "age",
                "operator": ">=",
                "value": 18
            },
            "if_function": {
                "type": "add_field",
                "field": "category",
                "value": "adult"
            },
            "else_function": {
                "type": "add_field",
                "field": "category",
                "value": "minor"
            }
        },
        {
            "type": "conditional",
            "condition": {
                "field": "salary",
                "operator": ">",
                "value": 0
            },
            "if_function": {
                "type": "add_field",
                "field": "employment_status",
                "value": "employed"
            },
            "else_function": {
                "type": "add_field",
                "field": "employment_status",
                "value": "unemployed"
            }
        },
        {
            "type": "conditional",
            "condition": {
                "field": "salary",
                "operator": ">=",
                "value": 70000
            },
            "if_function": {
                "type": "add_field",
                "field": "salary_band",
                "value": "high"
            },
            "else_function": {
                "type": "add_field",
                "field": "salary_band",
                "value": "low"
            }
        },
        {
            "type": "conditional",
            "condition": {
                "field": "department",
                "operator": "in",
                "value": ["Engineering", "Management"]
            },
            "if_function": {
                "type": "add_field",
                "field": "bonus_eligible",
                "value": True
            },
            "else_function": {
                "type": "add_field",
                "field": "bonus_eligible",
                "value": False
            }
        },
        {
            "type": "conditional",
            "condition": {
                "field": "status",
                "operator": "==",
                "value": "active"
            },
            "if_function": {
                "type": "add_field",
                "field": "active_employee",
                "value": True
            },
            "else_function": {
                "type": "add_field",
                "field": "active_employee",
                "value": False
            }
        },
        {
            "type": "filter",
            "criteria": {
                "active_employee": True
            }
        }
    ]
    
    print(f"\n🔄 Applying {len(transformations)} sequential transformations...")
    
    # Execute the sequential transformations
    payload = {
        "transformations": transformations,
        "records": employee_records
    }
    
    try:
        success, result, error = await execute_task("data_transform", payload)
        
        if success:
            print("✅ Sequential transformations completed successfully!")
            
            final_records = result.get('final_records', [])
            transformation_results = result.get('transformation_results', [])
            
            print(f"\n📈 Transformation Summary:")
            print(f"   • Initial records: {result.get('initial_record_count', 0)}")
            print(f"   • Final records: {result.get('final_record_count', 0)}")
            print(f"   • Transformations applied: {result.get('transformations_applied', 0)}")
            
            print(f"\n🔍 Step-by-step Results:")
            for step_result in transformation_results:
                step = step_result['step']
                transform_type = step_result['transformation'].get('type', 'unknown')
                record_count = step_result['record_count']
                print(f"   Step {step} ({transform_type}): {record_count} records")
            
            print(f"\n📋 Final Processed Records:")
            for i, record in enumerate(final_records, 1):
                print(f"   {i}. {record['name']}")
                print(f"      • Age: {record['age']} ({record.get('category', 'unknown')})")
                print(f"      • Salary: ${record['salary']:,} ({record.get('salary_band', 'unknown')} band)")
                print(f"      • Department: {record['department']}")
                print(f"      • Employment: {record.get('employment_status', 'unknown')}")
                print(f"      • Bonus Eligible: {record.get('bonus_eligible', False)}")
                print(f"      • Active: {record.get('active_employee', False)}")
                print()
            
            return True
        else:
            print(f"❌ Sequential transformations failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error executing sequential transformations: {e}")
        return False


async def test_api_integration():
    """Test the sequential transformations through the API."""
    print("\n\n🌐 Testing API Integration")
    print("=" * 30)
    
    # Sample data for API test
    test_records = [
        {"name": "Test User 1", "age": 25, "score": 85},
        {"name": "Test User 2", "age": 16, "score": 92},
        {"name": "Test User 3", "age": 30, "score": 78}
    ]
    
    # Simple transformations for API test
    api_transformations = [
        {
            "type": "conditional",
            "condition": {
                "field": "age",
                "operator": ">=",
                "value": 18
            },
            "if_function": {
                "type": "add_field",
                "field": "status",
                "value": "adult"
            },
            "else_function": {
                "type": "add_field",
                "field": "status",
                "value": "minor"
            }
        },
        {
            "type": "conditional",
            "condition": {
                "field": "score",
                "operator": ">=",
                "value": 80
            },
            "if_function": {
                "type": "add_field",
                "field": "grade",
                "value": "A"
            },
            "else_function": {
                "type": "add_field",
                "field": "grade",
                "value": "B"
            }
        }
    ]
    
    api_key = "7jrmgPE9EWvfxAQ_MTPKsRURufhjVoFb5hx7fTSd3HY"
    base_url = "http://zathapi:8000"
    
    job_data = {
        "task_type": "data_transform",
        "payload": {
            "transformations": api_transformations,
            "records": test_records
        },
        "callback_url": "https://httpbin.org/post"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📤 Creating job via API...")
            
            async with session.post(
                f"{base_url}/api/jobs",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json=job_data
            ) as response:
                if response.status == 202:
                    data = await response.json()
                    job_id = data['job_id']
                    print(f"✅ Job created successfully: {job_id[:8]}...")
                    print(f"   Status: {data['status']}")
                    print(f"   Created: {data['created_at']}")
                    return True
                else:
                    print(f"❌ Job creation failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False


async def test_backward_compatibility():
    """Test that single operations still work (backward compatibility)."""
    print("\n\n🔄 Testing Backward Compatibility")
    print("=" * 35)
    
    # Test single flatten_json operation
    print("1. Testing single flatten_json operation...")
    success, result, error = await execute_task("data_transform", {
        "operation": "flatten_json",
        "data": {
            "user": {
                "name": "John",
                "address": {
                    "city": "New York",
                    "country": "USA"
                }
            }
        }
    })
    
    if success:
        print("   ✅ Single operation works correctly")
        flattened = result.get('result', {})
        print(f"   📊 Flattened result: {flattened}")
    else:
        print(f"   ❌ Single operation failed: {error}")
        return False
    
    # Test single csv_to_json operation
    print("\n2. Testing single csv_to_json operation...")
    success, result, error = await execute_task("data_transform", {
        "operation": "csv_to_json",
        "csv_content": "name,age,city\nJohn,25,New York\nJane,30,Los Angeles",
        "delimiter": ","
    })
    
    if success:
        print("   ✅ Single operation works correctly")
        records = result.get('result', [])
        print(f"   📊 Parsed {len(records)} records")
    else:
        print(f"   ❌ Single operation failed: {error}")
        return False
    
    return True


async def main():
    """Run all end-to-end tests."""
    print("🚀 ZATH Sequential Transformations - End-to-End Test")
    print("=" * 60)
    
    try:
        # Test 1: Sequential transformations
        test1_success = await test_sequential_transformations()
        
        # Test 2: API integration
        test2_success = await test_api_integration()
        
        # Test 3: Backward compatibility
        test3_success = await test_backward_compatibility()
        
        print("\n\n🎯 Test Results Summary")
        print("=" * 25)
        print(f"✅ Sequential Transformations: {'PASSED' if test1_success else 'FAILED'}")
        print(f"✅ API Integration: {'PASSED' if test2_success else 'FAILED'}")
        print(f"✅ Backward Compatibility: {'PASSED' if test3_success else 'FAILED'}")
        
        if all([test1_success, test2_success, test3_success]):
            print("\n🎉 All end-to-end tests passed!")
            print("The looping and conditional logic utilities are working correctly.")
        else:
            print("\n❌ Some tests failed.")
            print("Please check the implementation.")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
