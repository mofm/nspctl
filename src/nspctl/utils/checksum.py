import errno
import functools
import hashlib
import os
import re
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

        return checksum.hexdigest(), size


_generate_hash_function("MD5", hashlib.md5, origin="hashlib")
_generate_hash_function("SHA1", hashlib.sha1, origin="hashlib")
_generate_hash_function("SHA256", hashlib.sha256, origin="hashlib")
_generate_hash_function("SHA512", hashlib.sha512, origin="hashlib")


class SizeHash:
    def checksum_file(self, filename):
        size = os.stat(filename).st_size
        return size, size


hashfunc_map["size"] = SizeHash()
hashfunc_keys = frozenset(hashfunc_map)


def perform_checksum(filename, hashname="MD5"):
    try:
        if hashname not in hashfunc_keys:
            raise Exception("{} , hash function not available".format(hashname))
        myhash, mysize = hashfunc_map[hashname].checksum_file(filename)
    except (OSError, IOError) as exc:
        if exc.errno in (errno.ENOENT, errno.ESTALE):
            raise Exception("{} : File not found".format(filename))
        elif exc.errno == errno.EACCES:
            raise Exception("{} : Permission denied".format(filename))
        raise
    return myhash, mysize


def verify_all(filename, mydict, strict=0):
    file_is_ok = True
    reason = "Reason unknown"
    try:
        mysize = os.stat(filename)[stat.ST_SIZE]
        if mydict.get("size") is not None and mydict["size"] != mysize:
            return False, (
                "File size does not match recorded size",
                mysize,
                mydict["size"],
            )
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            raise Exception("{}: File not found".format(filename))
        return False, (str(exc), None, None)

    verifiable_hash_types = set(mydict).intersection(hashfunc_keys)
    verifiable_hash_types.discard("size")
    if not verifiable_hash_types:
        expected = set(hashfunc_keys)
        expected.discard("size")
        expected = list(expected)
        expected.sort()
        expected = " ".join(expected)
        got = set(mydict)
        got.discard("size")
        got = list(got)
        got.sort()
        got = " ".join(got)
        return False, ("Insufficient data for checksum verification", got, expected)

    for x in sorted(mydict):
        if x == "size":
            continue
        elif x in hashfunc_keys:
            myhash = perform_checksum(filename, x)[0]
            if mydict[x] != myhash:
                if strict:
                    raise Exception(
                        ("Failed to verify '$(file)s' on " + "checksum type '%(type)s'")
                        % {"file": filename, "type": x}
                    )
                else:
                    file_is_ok = False
                    reason = (("Failed on {} verification".format(x)), myhash, mydict[x])
                    break

    return file_is_ok, reason


def perform_md5(filename):
    return perform_checksum(filename, "MD5")[0]


def perform_sha256(filename):
    return perform_checksum(filename, "SHA256")[0]


def perform_all(filename):
    mydict = {}
    for k in hashfunc_keys:
        mydict[k] = perform_checksum(filename, k)[0]
    return mydict


def get_valid_checksum_keys():
    return hashfunc_keys


def get_hash_origin(hashtype):
    if hashtype not in hashfunc_keys:
        raise KeyError(hashtype)
    return hashorigin_map.get(hashtype, "unknown")


def checksum_url(filename, hashname):
    if hashname not in hashfunc_keys:
        raise Exception("{} , hash does not supported".format(hashname))
    else:
        return [filename + "." + hashname.lower(), hashname.upper() + "SUMS"]


def parse_checksum(filename, sumsfile):
    if not os.path.exists(sumsfile):
        raise Exception("Checksum file {} does not exist".format(sumsfile))
    elif not os.path.isfile(sumsfile):
        raise Exception("Checksum file must be regular file")
    else:
        with open(sumsfile) as f:
            lines = [line.rstrip('\n') for line in f]
        checksum_map = []
        for line in lines:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                if parts[1].startswith((" ", "*",)):
                    parts[1] = parts[1][1:]

                checksum_map.append((parts[0], parts[1].lstrip("./")))

    for cksum in (s for (s, f) in checksum_map if f == filename):
        checksum = cksum
        break
    else:
        checksum = None

    if checksum is None:
        raise Exception("Unable to find a checksum for file '{}' in '{}'".format(filename, sumsfile))

    checksum = re.sub(r'\W', '', checksum).lower()
    try:
        int(checksum, 16)
    except ValueError:
        raise Exception("The checksum format is invalid")
    finally:
        os.remove(sumsfile)

    return checksum
