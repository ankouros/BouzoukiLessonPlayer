import logging
from pathlib import Path

from main import configure_logging


def test_configure_logging_rotates_log_file(tmp_path):
    log_file = tmp_path / "bouzouki_player.log"

    # Configure logging with a very small max_bytes so rotation happens quickly
    configure_logging(log_file=str(log_file), max_bytes=200, backup_count=1)

    logger = logging.getLogger()

    # Write enough log entries to exceed max_bytes
    for i in range(100):
        logger.error("This is a test log message number %d", i)

    # Base log file should exist
    assert log_file.exists()

    # With backup_count=1, a rotated file with suffix .1 should exist
    rotated = Path(str(log_file) + ".1")
    assert rotated.exists()

