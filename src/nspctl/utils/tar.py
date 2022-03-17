import logging
import tarfile

logger = logging.getLogger(__name__)


def tar_extract(filename, dest):
    try:
        with tarfile.open(filename, "r:*") as extract_me:
            logger.debug("Extracting '%s' to '%s'", filename, dest)
            extract_me.extractall(dest)
            logger.info("Extracted '%s' to '%s'", filename, dest)
            return True
    except (OSError, tarfile.TarError):
        return False
