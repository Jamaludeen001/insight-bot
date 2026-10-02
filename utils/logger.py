import logging
from datetime import datetime

def setup_logger():
    """Configure and return a logger instance"""
    logger = logging.getLogger('insight_bot')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(f'logs/insight_bot_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger