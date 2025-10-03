"""
Task handlers for different job types.

This module provides handlers for various task types that can be processed
by the job worker. Each handler is responsible for executing a specific
type of job and returning the result.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

# Import transform utilities for data_transform tasks
from transform_utils import flatten_json, csv_to_json, filter_records, aggregate

# Import logic utilities for advanced transformations
from logic_utils import (
        map_records, 
        conditional, 
        create_condition_function, 
        create_transform_function
    )

logger = logging.getLogger(__name__)


class TaskHandlerError(Exception):
    """Custom exception for task handler errors."""
    pass


async def handle_http_call(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle HTTP call tasks.
    
    This is the default handler that simulates HTTP operations.
    In a real implementation, this would make actual HTTP requests.
    
    Args:
        payload: Job payload containing HTTP call parameters
        
    Returns:
        Dictionary with execution result
        
    Raises:
        TaskHandlerError: If the HTTP call fails
    """
    logger.info("Processing HTTP call task")
    
    # Simulate HTTP call processing
    url = payload.get('url', 'https://example.com')
    method = payload.get('method', 'GET').upper()
    headers = payload.get('headers', {})
    data = payload.get('data', {})
    
    # Simulate processing delay
    await asyncio.sleep(1)
    
    # Simulate success response
    result = {
        'status': 'success',
        'url': url,
        'method': method,
        'response_code': 200,
        'response_time_ms': 150,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"HTTP call completed: {method} {url}")
    return result


async def handle_data_transform(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle data transformation tasks using transform_utils and logic_utils.
    
    Supports both single operations and sequential transformations.
    
    Args:
        payload: Job payload containing transformation parameters.
                Can contain:
                - 'operation': Single operation to perform
                - 'transformations': List of operations to perform sequentially
                - 'records': Data to transform (for sequential operations)
        
    Returns:
        Dictionary with transformation result
        
    Raises:
        TaskHandlerError: If the transformation fails
    """
    logger.info("Processing data transformation task")
    
    if not all([flatten_json, csv_to_json, filter_records, aggregate]):
        raise TaskHandlerError("Transform utilities not available")
    
    if not all([map_records, conditional, create_condition_function, create_transform_function]):
        raise TaskHandlerError("Logic utilities not available")
    
    try:
        # Check if this is a sequential transformation
        transformations = payload.get('transformations')
        if transformations:
            return await _handle_sequential_transformations(payload)
        
        # Handle single operation (backward compatibility)
        operation = payload.get('operation')
        if not operation:
            raise TaskHandlerError("Missing 'operation' in payload")
        
        return await _handle_single_operation(operation, payload)
    
    except Exception as e:
        if isinstance(e, TaskHandlerError):
            raise
        else:
            raise TaskHandlerError(f"Error in data transformation: {e}")


async def _handle_sequential_transformations(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle sequential transformations on a list of records.
    
    Args:
        payload: Job payload containing 'transformations' list and 'records'
        
    Returns:
        Dictionary with transformation results
    """
    transformations = payload.get('transformations', [])
    records = payload.get('records', [])
    
    if not transformations:
        raise TaskHandlerError("Missing 'transformations' in payload")
    
    if not records:
        raise TaskHandlerError("Missing 'records' in payload")
    
    if not isinstance(records, list):
        raise TaskHandlerError("Records must be a list for sequential transformations")
    
    if not isinstance(transformations, list):
        raise TaskHandlerError("Transformations must be a list")
    
    logger.info(f"Processing {len(transformations)} sequential transformations on {len(records)} records")
    
    current_records = records.copy()
    transformation_results = []
    
    for i, transform_spec in enumerate(transformations):
        logger.info(f"Executing transformation {i + 1}/{len(transformations)}: {transform_spec.get('type', 'unknown')}")
        
        try:
            result = await _execute_single_transformation(transform_spec, current_records)
            current_records = result.get('records', current_records)
            transformation_results.append({
                'step': i + 1,
                'transformation': transform_spec,
                'result': result,
                'record_count': len(current_records)
            })
        except Exception as e:
            logger.error(f"Error in transformation step {i + 1}: {e}")
            raise TaskHandlerError(f"Error in transformation step {i + 1}: {e}")
    
    return {
        'status': 'success',
        'operation': 'sequential_transformations',
        'transformations_applied': len(transformations),
        'initial_record_count': len(records),
        'final_record_count': len(current_records),
        'transformation_results': transformation_results,
        'final_records': current_records,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


async def _execute_single_transformation(transform_spec: Dict[str, Any], records: list) -> Dict[str, Any]:
    """
    Execute a single transformation step.
    
    Args:
        transform_spec: Transformation specification
        records: Current records to transform
        
    Returns:
        Dictionary with transformation result
    """
    transform_type = transform_spec.get('type')
    
    if transform_type == 'map':
        # Apply a function to each record
        func_spec = transform_spec.get('function')
        if not func_spec:
            raise TaskHandlerError("Map transformation requires 'function' specification")
        
        # Create the transformation function
        if isinstance(func_spec, dict):
            transform_func = create_transform_function(func_spec)
        else:
            raise TaskHandlerError("Function specification must be a dictionary")
        
        # Apply the function to all records
        transformed_records = map_records(records, transform_func)
        
        return {
            'type': 'map',
            'records': transformed_records,
            'transformed_count': len(transformed_records)
        }
    
    elif transform_type == 'conditional':
        # Apply conditional logic to each record
        condition_spec = transform_spec.get('condition')
        if_func_spec = transform_spec.get('if_function')
        else_func_spec = transform_spec.get('else_function')
        
        if not all([condition_spec, if_func_spec, else_func_spec]):
            raise TaskHandlerError("Conditional transformation requires 'condition', 'if_function', and 'else_function'")
        
        # Create the functions
        condition_func = create_condition_function(condition_spec)
        if_func = create_transform_function(if_func_spec)
        else_func = create_transform_function(else_func_spec)
        
        # Apply conditional logic to all records
        transformed_records = []
        for record in records:
            transformed_record = conditional(record, condition_func, if_func, else_func)
            transformed_records.append(transformed_record)
        
        return {
            'type': 'conditional',
            'records': transformed_records,
            'transformed_count': len(transformed_records)
        }
    
    elif transform_type == 'filter':
        # Filter records based on criteria
        criteria = transform_spec.get('criteria', {})
        if not criteria:
            raise TaskHandlerError("Filter transformation requires 'criteria'")
        
        filtered_records = filter_records(records, **criteria)
        
        return {
            'type': 'filter',
            'records': filtered_records,
            'filtered_count': len(filtered_records),
            'original_count': len(records)
        }
    
    elif transform_type == 'aggregate':
        # Aggregate records
        field = transform_spec.get('field')
        agg_type = transform_spec.get('agg_type', 'sum')
        
        if not field:
            raise TaskHandlerError("Aggregate transformation requires 'field'")
        
        result = aggregate(records, field, agg_type)
        
        return {
            'type': 'aggregate',
            'field': field,
            'agg_type': agg_type,
            'result': result,
            'record_count': len(records)
        }
    
    else:
        raise TaskHandlerError(f"Unknown transformation type: {transform_type}")


async def _handle_single_operation(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a single transformation operation (backward compatibility).
    
    Args:
        operation: Operation type
        payload: Operation payload
        
    Returns:
        Dictionary with operation result
    """
    if operation == 'flatten_json':
        data = payload.get('data', {})
        if not isinstance(data, dict):
            raise TaskHandlerError("Data must be a dictionary for flatten_json operation")
        
        result = flatten_json(data)
        return {
            'status': 'success',
            'operation': 'flatten_json',
            'result': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    elif operation == 'csv_to_json':
        csv_content = payload.get('csv_content', '')
        delimiter = payload.get('delimiter', ',')
        
        if not csv_content:
            raise TaskHandlerError("Missing 'csv_content' in payload")
        
        result = csv_to_json(csv_content, delimiter)
        return {
            'status': 'success',
            'operation': 'csv_to_json',
            'result': result,
            'record_count': len(result),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    elif operation == 'filter_records':
        records = payload.get('records', [])
        criteria = payload.get('criteria', {})
        
        if not records:
            raise TaskHandlerError("Missing 'records' in payload")
        if not criteria:
            raise TaskHandlerError("Missing 'criteria' in payload")
        
        result = filter_records(records, **criteria)
        return {
            'status': 'success',
            'operation': 'filter_records',
            'result': result,
            'filtered_count': len(result),
            'original_count': len(records),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    elif operation == 'aggregate':
        records = payload.get('records', [])
        field = payload.get('field', '')
        agg_type = payload.get('agg_type', 'sum')
        
        if not records:
            raise TaskHandlerError("Missing 'records' in payload")
        if not field:
            raise TaskHandlerError("Missing 'field' in payload")
        
        result = aggregate(records, field, agg_type)
        return {
            'status': 'success',
            'operation': 'aggregate',
            'field': field,
            'agg_type': agg_type,
            'result': result,
            'record_count': len(records),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    else:
        raise TaskHandlerError(f"Unknown operation: {operation}")


async def handle_email_send(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle email sending tasks.
    
    Args:
        payload: Job payload containing email parameters
        
    Returns:
        Dictionary with email sending result
        
    Raises:
        TaskHandlerError: If the email sending fails
    """
    logger.info("Processing email send task")
    
    to = payload.get('to')
    subject = payload.get('subject', '')
    body = payload.get('body', '')
    
    if not to:
        raise TaskHandlerError("Missing 'to' email address")
    
    # Simulate email sending
    await asyncio.sleep(0.5)
    
    result = {
        'status': 'success',
        'to': to,
        'subject': subject,
        'message_id': f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Email sent to {to}: {subject}")
    return result


async def handle_webhook_call(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle webhook call tasks.
    
    Args:
        payload: Job payload containing webhook parameters
        
    Returns:
        Dictionary with webhook call result
        
    Raises:
        TaskHandlerError: If the webhook call fails
    """
    logger.info("Processing webhook call task")
    
    url = payload.get('url')
    method = payload.get('method', 'POST').upper()
    headers = payload.get('headers', {})
    data = payload.get('data', {})
    
    if not url:
        raise TaskHandlerError("Missing 'url' for webhook call")
    
    # Simulate webhook call
    await asyncio.sleep(0.3)
    
    result = {
        'status': 'success',
        'url': url,
        'method': method,
        'response_code': 200,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Webhook called: {method} {url}")
    return result


async def handle_file_upload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle file upload tasks.
    
    Args:
        payload: Job payload containing file upload parameters
        
    Returns:
        Dictionary with file upload result
        
    Raises:
        TaskHandlerError: If the file upload fails
    """
    logger.info("Processing file upload task")
    
    file_path = payload.get('file_path')
    destination = payload.get('destination', 'storage/')
    
    if not file_path:
        raise TaskHandlerError("Missing 'file_path' for file upload")
    
    # Simulate file upload
    await asyncio.sleep(1.5)
    
    result = {
        'status': 'success',
        'file_path': file_path,
        'destination': destination,
        'file_size': payload.get('file_size', 1024),
        'upload_id': f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"File uploaded: {file_path} -> {destination}")
    return result


async def handle_report_generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle report generation tasks.
    
    Args:
        payload: Job payload containing report generation parameters
        
    Returns:
        Dictionary with report generation result
        
    Raises:
        TaskHandlerError: If the report generation fails
    """
    logger.info("Processing report generation task")
    
    report_type = payload.get('report_type', 'summary')
    data_source = payload.get('data_source', 'database')
    format_type = payload.get('format', 'pdf')
    
    # Simulate report generation
    await asyncio.sleep(2.0)
    
    result = {
        'status': 'success',
        'report_type': report_type,
        'data_source': data_source,
        'format': format_type,
        'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'file_size': 2048,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Report generated: {report_type} in {format_type} format")
    return result


# Task handler registry
TASK_HANDLERS = {
    'http_call': handle_http_call,
    'data_transform': handle_data_transform,
    'email_send': handle_email_send,
    'webhook_call': handle_webhook_call,
    'file_upload': handle_file_upload,
    'report_generate': handle_report_generate,
}


async def execute_task(task_type: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """
    Execute a task based on its type.
    
    Args:
        task_type: Type of task to execute
        payload: Task payload data
        
    Returns:
        Tuple of (success, result, error_message)
        - success: Boolean indicating if task succeeded
        - result: Task execution result (if successful)
        - error_message: Error message (if failed)
    """
    try:
        if task_type not in TASK_HANDLERS:
            error_msg = f"Unknown task type: {task_type}. Available types: {', '.join(TASK_HANDLERS.keys())}"
            logger.error(error_msg)
            return False, {}, error_msg
        
        handler = TASK_HANDLERS[task_type]
        logger.info(f"Executing task type: {task_type}")
        
        result = await handler(payload)
        logger.info(f"Task {task_type} completed successfully")
        
        return True, result, None
        
    except TaskHandlerError as e:
        error_msg = f"Task handler error: {str(e)}"
        logger.error(error_msg)
        return False, {}, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error in task {task_type}: {str(e)}"
        logger.error(error_msg)
        return False, {}, error_msg
