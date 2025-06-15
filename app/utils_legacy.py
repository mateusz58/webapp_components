"""Legacy utils - moved to services and utils modules.

This file is kept for backward compatibility.
New code should use the modular structure:
- app.utils.database for database operations
- app.services.csv_service for CSV processing
- app.utils.file_handling for file operations
"""

# Re-export commonly used functions for backward compatibility
from app.utils.database import get_or_create
from app.services.csv_service import CSVProcessingService

# Legacy function aliases
def process_csv_file(file_path):
    """Legacy function - use CSVProcessingService.process_csv_file instead."""
    return CSVProcessingService.process_csv_file(file_path)

def export_components_to_csv(file_path):
    """Legacy function - use CSVProcessingService.export_components_to_csv instead."""
    return CSVProcessingService.export_components_to_csv(file_path)

def create_sample_csv_data():
    """Legacy function - use CSVProcessingService.create_sample_csv_data instead."""
    return CSVProcessingService.create_sample_csv_data()