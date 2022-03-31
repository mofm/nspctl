import os


PROCFS_PATH = "/proc"
FILE_READ_BUFFER_SIZE = 32 * 1024


def pids():
    return [int(x) for x in os.listdir(PROCFS_PATH.encode()) if x.isdigit()]


class Process(object):
    """
    Linux Process class
    """
    def __init__(self, pid):
        self.pid = pid

    def parse_stat_file(self):
        """
        Return Process Stat File objects
        :return:
        """
        with open("%s/%s/stat" % (PROCFS_PATH, self.pid), "rb", buffering=FILE_READ_BUFFER_SIZE) as f:
            data = f.read()

        rpar = data.rfind(b')')
        name = data[data.find(b'(') + 1:rpar]
        fields = data[rpar + 2:].split()
        ret = {'name': name, 'status': fields[0], 'ppid': fields[1], 'ttynr': fields[4], 'utime': fields[11],
               'stime': fields[12], 'children_utime': fields[13], 'children_stime': fields[14],
               'create_time': fields[19], 'cpu_num': fields[36], 'blkio_ticks': fields[39]}

        return ret

    def cmdline(self):
        """
        Return pid cmdline
        """
        with open("%s/%s/cmdline" % (PROCFS_PATH, self.pid), "rt", buffering=FILE_READ_BUFFER_SIZE) as f:
            data = f.read()

        if not data:
            return []
        sep = '\x00' if data.endswith('\x00') else ' '

        if data.endswith(sep):
            data = data[:-1]
        cmdline = data.split(sep)

        if sep == "\x00" and len(cmdline) == 1 and ' ' in data:
            cmdline = data.split(' ')

        return cmdline
