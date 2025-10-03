#!/usr/bin/env python3
"""
Demonstration script for ZATH sequential transformations with looping and conditional logic.

This script shows how to use the new sequential transformation capabilities
to process complex data with multiple conditional steps and map operations.
"""

import asyncio
import json
from datetime import datetime, timezone

from workers.task_handlers import execute_task


async def demo_employee_processing():
    """Demonstrate employee data processing with sequential transformations."""
    print("🏢 Employee Data Processing Demo")
    print("=" * 40)
    
    # Sample employee data
    employees = [
        {"name": "Alice Johnson", "age": 28, "salary": 65000, "department": "Engineering", "years_experience": 5},
        {"name": "Bob Smith", "age": 22, "salary": 45000, "department": "Marketing", "years_experience": 1},
        {"name": "Carol Davis", "age": 35, "salary": 85000, "department": "Engineering", "years_experience": 10},
        {"name": "David Wilson", "age": 19, "salary": 0, "department": "Intern", "years_experience": 0},
        {"name": "Eva Brown", "age": 31, "salary": 72000, "department": "Management", "years_experience": 8}
    ]
    
    print(f"📊 Processing {len(employees)} employee records...")
    print("\nInitial Data:")
    for emp in employees:
        print(f"  • {emp['name']}: {emp['age']} years, ${emp['salary']:,}, {emp['department']}")
    
    # Define business logic transformations
    transformations = [
        # Step 1: Add processing timestamp
        {
            "type": "map",
            "function": {
                "type": "add_field",
                "field": "processed_at",
                "value": datetime.now(timezone.utc).isoformat()
            }
        },
        
        # Step 2: Categorize by age
        {
            "type": "conditional",
            "condition": {"field": "age", "operator": ">=", "value": 18},
            "if_function": {"type": "add_field", "field": "age_category", "value": "adult"},
            "else_function": {"type": "add_field", "field": "age_category", "value": "minor"}
        },
        
        # Step 3: Determine employment status
        {
            "type": "conditional",
            "condition": {"field": "salary", "operator": ">", "value": 0},
            "if_function": {"type": "add_field", "field": "employment_status", "value": "employed"},
            "else_function": {"type": "add_field", "field": "employment_status", "value": "unemployed"}
        },
        
        # Step 4: Calculate salary band
        {
            "type": "conditional",
            "condition": {"field": "salary", "operator": ">=", "value": 70000},
            "if_function": {"type": "add_field", "field": "salary_band", "value": "high"},
            "else_function": {"type": "add_field", "field": "salary_band", "value": "medium"}
        },
        
        # Step 5: Determine bonus eligibility
        {
            "type": "conditional",
            "condition": {"field": "department", "operator": "in", "value": ["Engineering", "Management"]},
            "if_function": {"type": "add_field", "field": "bonus_eligible", "value": True},
            "else_function": {"type": "add_field", "field": "bonus_eligible", "value": False}
        },
        
        # Step 6: Calculate experience level
        {
            "type": "conditional",
            "condition": {"field": "years_experience", "operator": ">=", "value": 5},
            "if_function": {"type": "add_field", "field": "experience_level", "value": "senior"},
            "else_function": {"type": "add_field", "field": "experience_level", "value": "junior"}
        },
        
        # Step 7: Filter to only employed adults
        {
            "type": "filter",
            "criteria": {
                "employment_status": "employed",
                "age_category": "adult"
            }
        }
    ]
    
    print(f"\n🔄 Applying {len(transformations)} transformations...")
    
    # Execute transformations
    payload = {
        "transformations": transformations,
        "records": employees
    }
    
    success, result, error = await execute_task("data_transform", payload)
    
    if success:
        final_records = result.get('final_records', [])
        
        print(f"\n✅ Processing completed!")
        print(f"📈 Results: {len(final_records)} employees after filtering")
        
        print(f"\n📋 Processed Employee Records:")
        for i, emp in enumerate(final_records, 1):
            print(f"\n  {i}. {emp['name']}")
            print(f"     Age: {emp['age']} ({emp['age_category']})")
            print(f"     Salary: ${emp['salary']:,} ({emp['salary_band']} band)")
            print(f"     Department: {emp['department']}")
            print(f"     Experience: {emp['years_experience']} years ({emp['experience_level']})")
            print(f"     Bonus Eligible: {emp['bonus_eligible']}")
            print(f"     Processed: {emp['processed_at'][:19]}")
        
        return True
    else:
        print(f"❌ Processing failed: {error}")
        return False


async def demo_sales_data_analysis():
    """Demonstrate sales data analysis with conditional logic."""
    print("\n\n📈 Sales Data Analysis Demo")
    print("=" * 30)
    
    # Sample sales data
    sales_data = [
        {"product": "Laptop", "quantity": 10, "price": 1200, "region": "North"},
        {"product": "Mouse", "quantity": 50, "price": 25, "region": "South"},
        {"product": "Keyboard", "quantity": 30, "price": 80, "region": "North"},
        {"product": "Monitor", "quantity": 5, "price": 300, "region": "East"},
        {"product": "Headphones", "quantity": 25, "price": 150, "region": "West"}
    ]
    
    print(f"📊 Analyzing {len(sales_data)} sales records...")
    
    # Sales analysis transformations
    transformations = [
        # Calculate total revenue
        {
            "type": "map",
            "function": {
                "type": "add_field",
                "field": "total_revenue",
                "value": "{quantity} * {price}"
            }
        },
        
        # Categorize by product type
        {
            "type": "conditional",
            "condition": {"field": "price", "operator": ">=", "value": 100},
            "if_function": {"type": "add_field", "field": "product_category", "value": "premium"},
            "else_function": {"type": "add_field", "field": "product_category", "value": "standard"}
        },
        
        # Determine sales volume
        {
            "type": "conditional",
            "condition": {"field": "quantity", "operator": ">=", "value": 30},
            "if_function": {"type": "add_field", "field": "volume_category", "value": "high"},
            "else_function": {"type": "add_field", "field": "volume_category", "value": "low"}
        },
        
        # Filter high-value products
        {
            "type": "filter",
            "criteria": {
                "product_category": "premium"
            }
        }
    ]
    
    print(f"\n🔄 Applying sales analysis transformations...")
    
    payload = {
        "transformations": transformations,
        "records": sales_data
    }
    
    success, result, error = await execute_task("data_transform", payload)
    
    if success:
        final_records = result.get('final_records', [])
        
        print(f"\n✅ Analysis completed!")
        print(f"📈 Results: {len(final_records)} premium products identified")
        
        print(f"\n📋 Premium Product Analysis:")
        for i, product in enumerate(final_records, 1):
            print(f"\n  {i}. {product['product']}")
            print(f"     Quantity: {product['quantity']} units")
            print(f"     Price: ${product['price']}")
            print(f"     Region: {product['region']}")
            print(f"     Category: {product['product_category']}")
            print(f"     Volume: {product['volume_category']}")
        
        return True
    else:
        print(f"❌ Analysis failed: {error}")
        return False


async def demo_simple_conditional_logic():
    """Demonstrate simple conditional logic with map operations."""
    print("\n\n🎯 Simple Conditional Logic Demo")
    print("=" * 35)
    
    # Simple user data
    users = [
        {"name": "John", "age": 25, "score": 85},
        {"name": "Jane", "age": 17, "score": 92},
        {"name": "Bob", "age": 30, "score": 78},
        {"name": "Alice", "age": 16, "score": 95}
    ]
    
    print(f"📊 Processing {len(users)} user records...")
    
    # Simple transformations
    transformations = [
        # Add status based on age
        {
            "type": "conditional",
            "condition": {"field": "age", "operator": ">=", "value": 18},
            "if_function": {"type": "add_field", "field": "status", "value": "adult"},
            "else_function": {"type": "add_field", "field": "status", "value": "minor"}
        },
        
        # Add grade based on score
        {
            "type": "conditional",
            "condition": {"field": "score", "operator": ">=", "value": 90},
            "if_function": {"type": "add_field", "field": "grade", "value": "A"},
            "else_function": {"type": "add_field", "field": "grade", "value": "B"}
        },
        
        # Filter to adults only
        {
            "type": "filter",
            "criteria": {"status": "adult"}
        }
    ]
    
    print(f"\n🔄 Applying simple conditional logic...")
    
    payload = {
        "transformations": transformations,
        "records": users
    }
    
    success, result, error = await execute_task("data_transform", payload)
    
    if success:
        final_records = result.get('final_records', [])
        
        print(f"\n✅ Processing completed!")
        print(f"📈 Results: {len(final_records)} adult users")
        
        print(f"\n📋 Adult User Records:")
        for i, user in enumerate(final_records, 1):
            print(f"  {i}. {user['name']} - Age: {user['age']}, Score: {user['score']}, Grade: {user['grade']}")
        
        return True
    else:
        print(f"❌ Processing failed: {error}")
        return False


async def main():
    """Run all demonstration scenarios."""
    print("🚀 ZATH Sequential Transformations - Complete Demo")
    print("=" * 55)
    
    try:
        # Demo 1: Employee processing
        demo1_success = await demo_employee_processing()
        
        # Demo 2: Sales data analysis
        demo2_success = await demo_sales_data_analysis()
        
        # Demo 3: Simple conditional logic
        demo3_success = await demo_simple_conditional_logic()
        
        print("\n\n🎯 Demo Results Summary")
        print("=" * 25)
        print(f"✅ Employee Processing: {'PASSED' if demo1_success else 'FAILED'}")
        print(f"✅ Sales Data Analysis: {'PASSED' if demo2_success else 'FAILED'}")
        print(f"✅ Simple Conditional Logic: {'PASSED' if demo3_success else 'FAILED'}")
        
        if all([demo1_success, demo2_success, demo3_success]):
            print("\n🎉 All demonstrations completed successfully!")
            print("\n📝 Key Features Demonstrated:")
            print("   • Sequential transformations with multiple steps")
            print("   • Conditional logic with if/else functions")
            print("   • Map operations to apply functions to all records")
            print("   • Filter operations to reduce record sets")
            print("   • Complex business logic with multiple conditions")
            print("   • Backward compatibility with single operations")
        else:
            print("\n❌ Some demonstrations failed.")
        
    except Exception as e:
        print(f"\n❌ Demo execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
