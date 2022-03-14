import errno
import functools
import hashlib
import os
import stat

hashfunc_map = {}
hashorigin_map = {}


def _open_file(filename):
    try:
        return open(
            filename, "rb"
        )
    except IOError as exc:
        func_call = "open('{}')".format(filename)
        if exc.errno == errno.EPERM:
            raise Exception("Operation not permitted: {}".format(func_call))
        elif exc.errno == errno.EACCES:
            raise Exception("Permission denied: {}".format(func_call))
        elif exc.errno == errno.ENOENT:
            raise Exception("File not found: {}".format(func_call))
        else:
            raise


class _generate_hash_function:

    __slots__ = ("_hashobject",)

    def __init__(self, hashtype, hashobject, origin="unknown"):
        self._hashobject = hashobject
        hashfunc_map[hashtype] = self
        hashorigin_map[hashtype] = origin

    def checksum_str(self, data):
        checksum = self._hashobject()
        checksum.update(data)
        return checksum.hexdigest()

    def checksum_file(self, filename):
        with _open_file(filename) as f:
            blocksize = 32768
            size = 0
            checksum = self._hashobject()
            data = f.read(blocksize)
            while data:
                checksum.update(data)
                size = size + len(data)
                data = f.read(blocksize)

        return (checksum.hexdigest(), size)


_generate_hash_function("MD5", hashlib.md5, origin="hashlib")
_generate_hash_function("SHA1", hashlib.sha1, origin="hashlib")
_generate_hash_function("SHA256", hashlib.sha256, origin="hashlib")
_generate_hash_function("SHA512", hashlib.sha512, origin="hashlib")


class SizeHash:
    def checksum_file(self, filename):
        size = os.stat(filename).st_size
        return (size, size)


hashfunc_keys = frozenset(hashfunc_map)


def perform_checksum(filename, hashname="MD5"):
    try:
        if hashname not in hashfunc_keys:
            raise Exception("{} ,hash function not available".format(hashname))
        myhash, mysize = hashfunc_map[hashname].checksum_file(filename)
    except (OSError, IOError) as exc:
        if exc.errno in (errno.ENOENT, errno.ESTALE):
            raise Exception("{} : File not found".format(filename))
        elif exc.errno == errno.EACCES:
            raise Exception("{} : Permission denied".format(filename))
        raise
    return myhash, mysize
