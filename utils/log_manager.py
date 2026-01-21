import logging
from collections import deque
from datetime import datetime

class LogBufferHandler(logging.Handler):
    def __init__(self, limit=50):
        super().__init__()
        self.buffer = deque(maxlen=limit)

    def emit(self, record):
        try:
            msg = self.format(record)
            time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            self.buffer.append({
                "time": time_str,
                "level": record.levelname,
                "msg": record.getMessage(),
                "color": self.get_color(record.levelname)
            })
        except Exception:
            self.handleError(record)

    def get_color(self, levelname):
        colors = {
            "DEBUG": "text-gray-400",
            "INFO": "text-blue-400",
            "WARNING": "text-yellow-400",
            "ERROR": "text-red-400",
            "CRITICAL": "text-red-600 font-bold",
            "SUCCESS": "text-green-400"
        }
        return colors.get(levelname, "text-blue-400")

    def get_logs(self):
        return list(self.buffer)

# Global instances
log_buffer_handler = LogBufferHandler(limit=100)
# Configure formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log_buffer_handler.setFormatter(formatter)

def setup_global_logging():
    root_logger = logging.getLogger()
    # Add our buffer handler to the root logger so it captures everything
    root_logger.addHandler(log_buffer_handler)
