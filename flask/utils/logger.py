import logging, time, sys
from pathlib import Path

class SessionLogger:
    def __init__(self, session_id: str, base_logger: logging.Logger):
        self.session_id = session_id
        self.logger = base_logger
        self.timer = None

    def info(self, msg, *args):
        self.logger.info(f"[{self.session_id}] {msg}", *args)

    def error(self, msg, *args):
        self.logger.error(f"[{self.session_id}] {msg}", *args)

    def exception(self, msg, *args):
        self.logger.exception(f"[{self.session_id}] {msg}", *args)

    def start_timer(self):
        self.timer = time.time()

    def log_time(self, label: str):
        if self.timer is None:
            self.info(f"⏱️ Timer not started for: {label}")
        else:
            duration = time.time() - self.timer
            self.info(f"{label} in {duration:.3f} sec")
            self.timer = time.time()  # auto-reset

class LogManager:
    def __init__(self, logger_name="Echo", log_path="/", log_file="main.log", uuid=None):
        self.log_path = log_path
        self.log_file = log_file
        self.uuid = uuid
        self.root_logger = logging.getLogger(logger_name)
        self.root_logger.setLevel(logging.DEBUG)

    def get_session_logger(self) -> SessionLogger:
        log_path = Path(f"{self.log_path}{self.log_file}")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Avoid duplicate handlers
        logger = logging.getLogger(f"session-{self.uuid}")
        if not logger.handlers:
            file_handler = logging.FileHandler(log_path)
            stream_handler = logging.StreamHandler(sys.stdout)

            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            file_handler.setFormatter(formatter)
            stream_handler.setFormatter(formatter)

            logger.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)

        return SessionLogger(session_id=self.uuid, base_logger=logger)
