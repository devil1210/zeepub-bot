import logging
import json
from datetime import datetime

class StructuredLogger:
    """Logger con formato JSON estructurado."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_event(self, level: str, event: str, **kwargs):
        """Registra evento con metadatos estructurados."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event": event,
            "data": kwargs
        }
        
        # Avoid double encoding if handler already does formatting, 
        # but typical python logging handles strings.
        # We invoke the standard logger methods.
        getattr(self.logger, level.lower())(json.dumps(log_entry))
    
    def log_download(self, user_id: int, book_title: str, success: bool):
        """Log específico para descargas."""
        self.log_event(
            "info",
            "book_download",
            user_id=user_id,
            book=book_title,
            success=success
        )
