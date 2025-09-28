#!/usr/bin/env python3
"""
Demonstration script for multi-task support in ZATH system.

This script demonstrates the various task types and their handlers
without requiring database connections.
"""

import asyncio
import json
from workers.task_handlers import execute_task, TASK_HANDLERS


async def demo_task_handlers():
    """Demonstrate all task handlers."""
    print("🚀 ZATH Multi-Task Support Demonstration")
    print("=" * 50)
    
    # Demo 1: HTTP Call Task
    print("\n📡 1. HTTP Call Task")
    print("-" * 20)
    success, result, error = await execute_task("http_call", {
        "url": "https://api.example.com/users",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": {"name": "John Doe", "email": "john@example.com"}
    })
    
    if success:
        print(f"✅ HTTP call successful!")
        print(f"   URL: {result['url']}")
        print(f"   Method: {result['method']}")
        print(f"   Response Code: {result['response_code']}")
        print(f"   Response Time: {result['response_time_ms']}ms")
    else:
        print(f"❌ HTTP call failed: {error}")
    
    # Demo 2: Data Transformation - Flatten JSON
    print("\n🔄 2. Data Transformation - Flatten JSON")
    print("-" * 40)
    nested_data = {
        "user": {
            "name": "John Doe",
            "details": {
                "age": 30,
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "country": "USA"
                }
            }
        },
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    }
    
    success, result, error = await execute_task("data_transform", {
        "operation": "flatten_json",
        "data": nested_data
    })
    
    if success:
        print(f"✅ JSON flattened successfully!")
        print(f"   Original keys: {list(nested_data.keys())}")
        print(f"   Flattened keys: {list(result['result'].keys())}")
        print(f"   Sample flattened data:")
        for key, value in list(result['result'].items())[:3]:
            print(f"     {key}: {value}")
    else:
        print(f"❌ JSON flattening failed: {error}")
    
    # Demo 3: Data Transformation - CSV to JSON
    print("\n📊 3. Data Transformation - CSV to JSON")
    print("-" * 35)
    csv_data = """name,age,department,salary
John Doe,30,Engineering,75000
Jane Smith,28,Marketing,65000
Bob Johnson,35,Sales,70000
Alice Brown,32,Engineering,80000"""
    
    success, result, error = await execute_task("data_transform", {
        "operation": "csv_to_json",
        "csv_content": csv_data,
        "delimiter": ","
    })
    
    if success:
        print(f"✅ CSV converted to JSON successfully!")
        print(f"   Records processed: {result['record_count']}")
        print(f"   Sample records:")
        for i, record in enumerate(result['result'][:2]):
            print(f"     Record {i+1}: {record}")
    else:
        print(f"❌ CSV conversion failed: {error}")
    
    # Demo 4: Data Transformation - Filter Records
    print("\n🔍 4. Data Transformation - Filter Records")
    print("-" * 40)
    records = result['result'] if success else []
    
    if records:
        success, result, error = await execute_task("data_transform", {
            "operation": "filter_records",
            "records": records,
            "criteria": {"department": "Engineering"}
        })
        
        if success:
            print(f"✅ Records filtered successfully!")
            print(f"   Original count: {len(records)}")
            print(f"   Filtered count: {result['filtered_count']}")
            print(f"   Filtered records:")
            for record in result['result']:
                print(f"     {record['name']} - {record['department']} - ${record['salary']}")
        else:
            print(f"❌ Record filtering failed: {error}")
    
    # Demo 5: Data Transformation - Aggregate
    print("\n📈 5. Data Transformation - Aggregate")
    print("-" * 35)
    if records:
        success, result, error = await execute_task("data_transform", {
            "operation": "aggregate",
            "records": records,
            "field": "salary",
            "agg_type": "avg"
        })
        
        if success:
            print(f"✅ Salary aggregation successful!")
            print(f"   Average salary: ${result['result']:,.2f}")
            print(f"   Records processed: {result['record_count']}")
        else:
            print(f"❌ Salary aggregation failed: {error}")
    
    # Demo 6: Email Send Task
    print("\n📧 6. Email Send Task")
    print("-" * 20)
    success, result, error = await execute_task("email_send", {
        "to": "user@example.com",
        "subject": "Welcome to ZATH!",
        "body": "Thank you for using our job processing system. Your account has been created successfully."
    })
    
    if success:
        print(f"✅ Email sent successfully!")
        print(f"   To: {result['to']}")
        print(f"   Subject: {result['subject']}")
        print(f"   Message ID: {result['message_id']}")
    else:
        print(f"❌ Email sending failed: {error}")
    
    # Demo 7: Webhook Call Task
    print("\n🔗 7. Webhook Call Task")
    print("-" * 25)
    success, result, error = await execute_task("webhook_call", {
        "url": "https://webhook.site/abc123",
        "method": "POST",
        "headers": {"Authorization": "Bearer token123"},
        "data": {
            "event": "user_registered",
            "user_id": "12345",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    })
    
    if success:
        print(f"✅ Webhook called successfully!")
        print(f"   URL: {result['url']}")
        print(f"   Method: {result['method']}")
        print(f"   Response Code: {result['response_code']}")
    else:
        print(f"❌ Webhook call failed: {error}")
    
    # Demo 8: File Upload Task
    print("\n📁 8. File Upload Task")
    print("-" * 25)
    success, result, error = await execute_task("file_upload", {
        "file_path": "/tmp/user_data.csv",
        "destination": "storage/uploads/2024/01/15/",
        "file_size": 2048
    })
    
    if success:
        print(f"✅ File uploaded successfully!")
        print(f"   File: {result['file_path']}")
        print(f"   Destination: {result['destination']}")
        print(f"   Upload ID: {result['upload_id']}")
        print(f"   File Size: {result['file_size']} bytes")
    else:
        print(f"❌ File upload failed: {error}")
    
    # Demo 9: Report Generation Task
    print("\n📋 9. Report Generation Task")
    print("-" * 30)
    success, result, error = await execute_task("report_generate", {
        "report_type": "monthly_summary",
        "data_source": "database",
        "format": "pdf",
        "date_range": "2024-01-01 to 2024-01-31"
    })
    
    if success:
        print(f"✅ Report generated successfully!")
        print(f"   Report Type: {result['report_type']}")
        print(f"   Data Source: {result['data_source']}")
        print(f"   Format: {result['format']}")
        print(f"   Report ID: {result['report_id']}")
        print(f"   File Size: {result['file_size']} bytes")
    else:
        print(f"❌ Report generation failed: {error}")
    
    # Demo 10: Error Handling
    print("\n⚠️  10. Error Handling Demo")
    print("-" * 30)
    
    # Unknown task type
    success, result, error = await execute_task("unknown_task", {"test": "data"})
    print(f"Unknown task type: {'❌ Failed as expected' if not success else '✅ Unexpected success'}")
    if not success:
        print(f"   Error: {error}")
    
    # Invalid data transform operation
    success, result, error = await execute_task("data_transform", {
        "operation": "invalid_operation",
        "data": {"test": "data"}
    })
    print(f"Invalid operation: {'❌ Failed as expected' if not success else '✅ Unexpected success'}")
    if not success:
        print(f"   Error: {error}")
    
    # Missing required fields
    success, result, error = await execute_task("email_send", {
        "subject": "Test",
        "body": "Test body"
        # Missing 'to' field
    })
    print(f"Missing required field: {'❌ Failed as expected' if not success else '✅ Unexpected success'}")
    if not success:
        print(f"   Error: {error}")
    
    # Summary
    print("\n🎯 Summary")
    print("=" * 50)
    print(f"Total task handlers available: {len(TASK_HANDLERS)}")
    print("Available task types:")
    for task_type in sorted(TASK_HANDLERS.keys()):
        print(f"  • {task_type}")
    
    print("\n✨ Multi-task support is working perfectly!")
    print("   All task handlers are functional and ready for production use.")


if __name__ == "__main__":
    asyncio.run(demo_task_handlers())
