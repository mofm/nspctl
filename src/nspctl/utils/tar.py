import logging
import tarfile

logger = logging.getLogger(__name__)


def tar_extract(filename, dest):
    try:
        with tarfile.open(filename, "r:*") as extract_me:
            logger.debug("Extracting '%s' to '%s'", filename, dest)
            
            import os
            
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(extract_me, dest)
            logger.info("Extracted '%s' to '%s'", filename, dest)
            return True
    except (OSError, tarfile.TarError):
        return False
