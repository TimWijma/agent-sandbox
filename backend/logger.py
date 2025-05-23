import logging

logger = logging.getLogger("agent-sandbox")
logger.setLevel(logging.INFO)

# handler = logging.StreamHandler()
file_handler = logging.FileHandler("agent-sandbox.log")

formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)