import logging

from pathlib import Path
# Todo Actually implement this instead of printing to console

def log(msg):
    LogsDirectory = Path(__file__).resolve().parent.parent/Path("LOGS")
    if not LogsDirectory.exists():
        LogsDirectory.mkdir()

    logger = logging.getLogger(__name__)
    logger.propagate = False

    logger.setLevel(logging.DEBUG)

    # create a file handler

    loggingHandler = logging.FileHandler(LogsDirectory/Path('Bot.log'))
    # create a logging format
    LoggingFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    loggingHandler.setFormatter(LoggingFormatter)

    logger.addHandler(loggingHandler)

    # Log Message
    logger.debug(msg)


if __name__ == "__main__":
    log("Test")
    log("Test2")
    log("Test3")
