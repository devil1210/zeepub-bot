import logging
from collections import deque
from datetime import datetime

class LogBufferHandler(logging.Handler):
    def __init__(self, limit=2000):
        super().__init__()
        self.buffer = deque(maxlen=limit)

    def emit(self, record):
        try:
            msg = self.format(record)
            # Store unix timestamp for filtering
            timestamp = record.created 
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            
            self.buffer.append({
                "time": time_str,
                "timestamp": timestamp,
                "level": record.levelname,
                "msg": record.getMessage(),
                "color": self.get_color(record.levelname),
                "logger": record.name
            })
        except Exception:
            self.handleError(record)

    def get_color(self, levelname):
        colors = {
            "DEBUG": "text-gray-500 opacity-70",
            "INFO": "text-blue-400",
            "WARNING": "text-yellow-400",
            "ERROR": "text-red-400",
            "CRITICAL": "text-red-600 font-bold",
            "SUCCESS": "text-green-400"
        }
        return colors.get(levelname, "text-blue-400")

    def get_logs(self, level=None, last_hours=None):
        logs = list(self.buffer)
        
        if last_hours:
            cutoff = datetime.now().timestamp() - (last_hours * 3600)
            logs = [log for log in logs if log["timestamp"] >= cutoff]
            
        if level and level != "ALL":
            # Map levels so we show 'higher' levels too if requested? 
            # Usually users want EXACT level or 'that level and above'.
            # Let's do exact comparison or 'above' based on standard logging levels.
            level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
            min_val = level_map.get(level, 0)
            logs = [log for log in logs if level_map.get(log["level"], 0) >= min_val]
            
        return logs

# Global instances
log_buffer_handler = LogBufferHandler(limit=2000)
# Configure formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log_buffer_handler.setFormatter(formatter)

def setup_global_logging():
    root_logger = logging.getLogger()
    # Add our buffer handler to the root logger so it captures everything
    root_logger.addHandler(log_buffer_handler)
