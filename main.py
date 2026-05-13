from logger import get_logger
from pipeline import run

logger = get_logger()


if __name__ == "__main__":
    try:
        run()
    except Exception:
        logger.exception("Pipeline crashed")
        raise
