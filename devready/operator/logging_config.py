import logging
import re
from typing import Optional

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = re.sub(r'(bearer|token|key|password)[=:]\s*\S+', r'\1=***', record.msg, flags=re.I)
        return True

def configure_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    logger = logging.getLogger('devready.operator')
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
    
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    ch.addFilter(SensitiveDataFilter())
    logger.addHandler(ch)
    
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        fh.addFilter(SensitiveDataFilter())
        logger.addHandler(fh)
