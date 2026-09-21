import asyncio
import logging

from config import settings
from edge_worker import EdgeWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sentira-edge")

if __name__ == "__main__":
    try:
        asyncio.run(EdgeWorker().run())
    except KeyboardInterrupt:
        logger.info("edge connector stopped")
