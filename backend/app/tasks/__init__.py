"""
Async tasks for document processing
"""
from .document_tasks import detect_columns_task, extract_data_task

__all__ = ['detect_columns_task', 'extract_data_task']
