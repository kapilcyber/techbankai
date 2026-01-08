import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'app_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

def get_logger(name: str):
    """Get logger instance"""
    return logging.getLogger(name)
