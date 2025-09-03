import logging
import os

logger = logging.getLogger("agent-sandbox")
logger.setLevel(logging.INFO)

current_file_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_file_dir, "agent-sandbox.log")

file_handler = logging.FileHandler(log_file_path)

formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
