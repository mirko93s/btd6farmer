# import logging

from pathlib import Path

LogsDirectory = Path(__file__).resolve().parent.parent/Path("LOGS")

if not LogsDirectory.exists():
    LogsDirectory.mkdir()

import logging

logger = logging
logger.basicConfig(filename=LogsDirectory/Path('Bot.log'), format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

if __name__ == "__main__":
    logger.warning("test")
    logger.warning("test 2")
    logger.warning("test 3")
