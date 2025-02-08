import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from colorama import Fore, Back, Style, init
from config.settings import Config

# Initialize colorama for cross-platform colored output
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored console output"""
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }

    def format(self, record):
        if not hasattr(record, 'color'):
            record.color = self.COLORS.get(record.levelname, '')
        record.reset = Style.RESET_ALL
        
        if record.levelno == logging.DEBUG:
            record.msg = f"[Process: {record.process}|Thread: {record.threadName}] {record.msg}"
            
        return super().format(record)

def setup_logger(name: str = "BigYellowJacket"):
    """Setup application logger with console and file handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOGGING.LEVEL)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s %(color)s[%(levelname)s]%(reset)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console_handler)

    # File handler with rotation
    log_file = Path(Config.LOGGING.FILE)
    log_file.parent.mkdir(exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=Config.LOGGING.MAX_SIZE,
        backupCount=Config.LOGGING.BACKUP_COUNT
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)

    return logger

# Create the default logger instance
logger = setup_logger()