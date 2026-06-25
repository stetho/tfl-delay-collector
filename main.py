"""
Entry point for the TfL delay collector.
"""

import logging
import sys

from collector.scheduler import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

if __name__ == "__main__":
    run()
