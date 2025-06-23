"""Database utilities."""

from app import db
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from typing import Any, Optional, List, Dict


def get_or_create(model, **kwargs) -> tuple:
    """
    Get an instance of a model, or create it if it doesn't exist.
    Returns (instance, created) tuple.
    """
    try:
        instance = model.query.filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            instance = model(**kwargs)
            db.session.add(instance)
            db.session.commit()
            return instance, True
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in get_or_create: {str(e)}")
        raise


def safe_commit() -> bool:
    """Safely commit database changes with rollback on error."""
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database commit error: {str(e)}")
        return False


def safe_delete(instance) -> bool:
    """Safely delete an instance with rollback on error."""
    try:
        db.session.delete(instance)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database delete error: {str(e)}")
        return False


def safe_bulk_insert(model, data_list: List[Dict]) -> tuple:
    """
    Safely bulk insert data.
    Returns (success_count, error_count, errors) tuple.
    """
    success_count = 0
    error_count = 0
    errors = []
    
    for data in data_list:
        try:
            instance = model(**data)
            db.session.add(instance)
            db.session.commit()
            success_count += 1
        except SQLAlchemyError as e:
            db.session.rollback()
            error_count += 1
            errors.append(f"Error inserting {data}: {str(e)}")
            current_app.logger.error(f"Bulk insert error: {str(e)}")
    
    return success_count, error_count, errors


def safe_bulk_update(instances_data: List[tuple]) -> tuple:
    """
    Safely bulk update instances.
    instances_data: List of (instance, update_data) tuples
    Returns (success_count, error_count, errors) tuple.
    """
    success_count = 0
    error_count = 0
    errors = []
    
    for instance, update_data in instances_data:
        try:
            for key, value in update_data.items():
                setattr(instance, key, value)
            db.session.commit()
            success_count += 1
        except SQLAlchemyError as e:
            db.session.rollback()
            error_count += 1
            errors.append(f"Error updating {instance}: {str(e)}")
            current_app.logger.error(f"Bulk update error: {str(e)}")
    
    return success_count, error_count, errors


def safe_bulk_delete(instances: List[Any]) -> tuple:
    """
    Safely bulk delete instances.
    Returns (success_count, error_count, errors) tuple.
    """
    success_count = 0
    error_count = 0
    errors = []
    
    for instance in instances:
        try:
            db.session.delete(instance)
            db.session.commit()
            success_count += 1
        except SQLAlchemyError as e:
            db.session.rollback()
            error_count += 1
            errors.append(f"Error deleting {instance}: {str(e)}")
            current_app.logger.error(f"Bulk delete error: {str(e)}")
    
    return success_count, error_count, errors


def paginate_query(query, page: int = 1, per_page: int = 20, error_out: bool = False):
    """Paginate a query with error handling."""
    try:
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=error_out
        )
    except Exception as e:
        current_app.logger.error(f"Pagination error: {str(e)}")
        # Return empty pagination object
        from sqlalchemy import text
        empty_query = db.session.query(text("1")).filter(text("1=0"))
        return empty_query.paginate(page=1, per_page=per_page, error_out=False)


def execute_raw_sql(sql: str, params: Optional[Dict] = None) -> Optional[Any]:
    """Execute raw SQL with error handling."""
    try:
        from sqlalchemy import text
        result = db.session.execute(text(sql), params or {})
        db.session.commit()
        return result
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Raw SQL execution error: {str(e)}")
        return None


def get_table_row_count(model) -> int:
    """Get the row count for a model/table."""
    try:
        return db.session.query(model).count()
    except SQLAlchemyError as e:
        current_app.logger.error(f"Row count error: {str(e)}")
        return 0


def backup_table_data(model, limit: Optional[int] = None) -> List[Dict]:
    """Backup table data to a list of dictionaries."""
    try:
        query = db.session.query(model)
        if limit:
            query = query.limit(limit)
        
        instances = query.all()
        backup_data = []
        
        for instance in instances:
            # Convert instance to dict (assumes model has __dict__ or to_dict method)
            if hasattr(instance, 'to_dict'):
                backup_data.append(instance.to_dict())
            else:
                # Fallback to using __dict__ but filter out SQLAlchemy internal attrs
                data = {k: v for k, v in instance.__dict__.items() 
                       if not k.startswith('_')}
                backup_data.append(data)
        
        return backup_data
    except SQLAlchemyError as e:
        current_app.logger.error(f"Backup error: {str(e)}")
        return []


class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            db.session.rollback()
            current_app.logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            try:
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(f"Transaction commit failed: {str(e)}")
                raise