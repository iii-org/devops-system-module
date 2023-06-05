import logging
from logging import handlers
import os

if not os.path.exists("logs"):
    os.makedirs("logs")

handler = handlers.TimedRotatingFileHandler(
    "logs/devops-api.log", when="D", interval=1, backupCount=14, encoding="utf-8"
)
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(user_name)s/%(user_id)d %(filename)s" " [line:%(lineno)d] %(levelname)s %(message)s",
        "%Y %b %d, %a %H:%M:%S",
    )
)
logger = logging.getLogger("devops.api")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
