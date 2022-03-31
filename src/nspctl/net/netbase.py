import fcntl
import os
import re
import socket
import struct
import ctypes
import array
import math


SYSFS_NET_PATH = b"/sys/class/net"
PROCFS_NET_PATH = b"/proc/net/dev"

# From linux/sockios.h
SIOCGIFCONF = 0x8912
SIOCGIFINDEX = 0x8933
SIOCGIFFLAGS = 0x8913
SIOCSIFFLAGS = 0x8914
SIOCGIFHWADDR = 0x8927
SIOCSIFHWADDR = 0x8924
SIOCGIFADDR = 0x8915
SIOCSIFADDR = 0x8916
SIOCGIFNETMASK = 0x891B
SIOCSIFNETMASK = 0x891C
SIOCETHTOOL = 0x8946

# From linux/if.h
IFF_UP = 0x1

# From linux/socket.h
AF_UNIX = 1
AF_INET = 2

# From linux/ethtool.h
ETHTOOL_GSET = 0x00000001
ETHTOOL_SSET = 0x00000002
ETHTOOL_GLINK = 0x0000000a
ETHTOOL_SPAUSEPARAM = 0x00000013

ADVERTISED_10baseT_Half = (1 << 0)
ADVERTISED_10baseT_Full = (1 << 1)
ADVERTISED_100baseT_Half = (1 << 2)
ADVERTISED_100baseT_Full = (1 << 3)
ADVERTISED_1000baseT_Half = (1 << 4)
ADVERTISED_1000baseT_Full = (1 << 5)
ADVERTISED_Autoneg = (1 << 6)
ADVERTISED_TP = (1 << 7)
ADVERTISED_AUI = (1 << 8)
ADVERTISED_MII = (1 << 9)
ADVERTISED_FIBRE = (1 << 10)
ADVERTISED_BNC = (1 << 11)
ADVERTISED_10000baseT_Full = (1 << 12)

# This is probably not cross-platform
SIZE_OF_IFREQ = 40

# Globals
sock = None
sockfd = None

if not os.path.isdir(SYSFS_NET_PATH):
    raise Exception("'{}': sysfs path not found".format(SYSFS_NET_PATH))
if not os.path.exists(PROCFS_NET_PATH):
    raise Exception("'{}': procfs path not found".format(PROCFS_NET_PATH))


class Interface(object):
    """
    Common class for Linux network devices
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<{} {} at 0x{}>".format(self.__class__.__name__, self.name, id(self))

    def up(self):
        """
        Up the bridge interface
        """
        ifreq = struct.pack('16sh', self.name, 0)
        flags = struct.unpack('16sh', fcntl.ioctl(sockfd, SIOCGIFFLAGS, ifreq))[1]

        # Set new flags
        flags = flags | IFF_UP
        ifreq = struct.pack('16sh', self.name, flags)
        fcntl.ioctl(sockfd, SIOCSIFFLAGS, ifreq)

    def down(self):
        """
        Down the bridge interface
        """
        ifreq = struct.pack('16sh', self.name, 0)
        flags = struct.unpack('16sh', fcntl.ioctl(sockfd, SIOCGIFFLAGS, ifreq))[1]

        # Set new flags
        flags = flags & ~IFF_UP
        ifreq = struct.pack('16sh', self.name, flags)
        fcntl.ioctl(sockfd, SIOCSIFFLAGS, ifreq)

    def is_up(self):
        """
        Return interface status
        """
        ifreq = struct.pack('16sh', self.name, 0)
        flags = struct.unpack('16sh', fcntl.ioctl(sockfd, SIOCGIFFLAGS, ifreq))[1]

        # Set new flags
        if flags & IFF_UP:
            return True
        else:
            return False

    def get_mac(self):
        """
        Obtain the interface mac address
        """
        ifreq = struct.pack('16sH14s', self.name, AF_UNIX, b'\x00' * 14)
        res = fcntl.ioctl(sockfd, SIOCGIFHWADDR, ifreq)
        address = struct.unpack('16sH14s', res)[2]
        mac = struct.unpack('6B8x', address)

        return ":".join(['%02X' % i for i in mac])

    def set_mac(self, newmac):
        """
        Set the new mac address to interface
        """
        macbytes = [int(i, 16) for i in newmac.split(':')]
        ifreq = struct.pack('16sH6B8x', self.name, AF_UNIX, *macbytes)
        fcntl.ioctl(sockfd, SIOCSIFHWADDR, ifreq)

    def get_ip(self):
        """
        Get the interface IP address
        """
        ifreq = struct.pack('16sH14s', self.name, AF_INET, b'\x00' * 14)
        try:
            res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
        except IOError:
            return None
        ip = struct.unpack('16sH2x4s8x', res)[2]

        return socket.inet_ntoa(ip)

    def set_ip(self, newip):
        """
        Set the new IP address
        """
        ipbytes = socket.inet_aton(newip)
        ifreq = struct.pack('16sH2s4s8s', self.name, AF_INET, b'\x00' * 2, ipbytes, b'\x00' * 8)
        fcntl.ioctl(sockfd, SIOCSIFADDR, ifreq)

    def get_netmask(self):
        """
        Get the IP netmask address
        """
        ifreq = struct.pack('16sH14s', self.name, AF_INET, b'\x00' * 14)
        try:
            res = fcntl.ioctl(sockfd, SIOCGIFNETMASK, ifreq)
        except IOError:
            return 0
        netmask = socket.ntohl(struct.unpack('16sH2xI8x', res)[2])

        return 32 - int(round(
            math.log(ctypes.c_uint32(~netmask).value + 1, 2), 1))

    def set_netmask(self, netmask):
        """
        Set the new IP netmask address
        """
        netmask = ctypes.c_uint32(~((2 ** (32 - netmask)) - 1)).value
        nmbytes = socket.htonl(netmask)
        ifreq = struct.pack('16sH2sI8s', self.name, AF_INET, b'\x00' * 2, nmbytes, b'\x00' * 8)
        fcntl.ioctl(sockfd, SIOCSIFNETMASK, ifreq)

    def get_index(self):
        """
        Convert an interface name to a index value
        """
        ifreq = struct.pack('16si', self.name, 0)
        res = fcntl.ioctl(sockfd, SIOCGIFINDEX, ifreq)
        return struct.unpack("16si", res)[1]

    def get_link_info(self):
        """
        Get the interface link info
        """
        ecmd = array.array('B', struct.pack('I39s', ETHTOOL_GSET, b'\x00' * 39))
        ifreq = struct.pack('16sP', self.name, ecmd.buffer_info()[0])
        try:
            fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)
            res = ecmd.tostring()
            speed, duplex, auto = struct.unpack('12xHB3xB24x', res)
        except IOError:
            speed, duplex, auto = 65535, 255, 255

        # Then get link up/down state
        ecmd = array.array('B', struct.pack('2I', ETHTOOL_GLINK, 0))
        ifreq = struct.pack('16sP', self.name, ecmd.buffer_info()[0])
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)
        res = ecmd.tostring()
        up = bool(struct.unpack('4xI', res)[0])

        if speed == 65535:
            speed = 0
        if duplex == 255:
            duplex = None
        else:
            duplex = bool(duplex)
        if auto == 255:
            auto = None
        else:
            auto = bool(auto)
        return speed, duplex, auto, up

    def set_link_mode(self, speed, duplex):
        """
        Set the link mode
        """
        ecmd = array.array('B', struct.pack('I39s', ETHTOOL_GSET, b'\x00' * 39))
        ifreq = struct.pack('16sP', self.name, ecmd.buffer_info()[0])
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)
        # Then modify it to reflect our needs
        ecmd[0:4] = array.array('B', struct.pack('I', ETHTOOL_SSET))
        ecmd[12:14] = array.array('B', struct.pack('H', speed))
        ecmd[14] = int(duplex)
        ecmd[18] = 0  # Autonegotiation is off
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)

    def set_link_auto(self, ten=True, hundred=True, thousand=True):
        """
        Set the link auto
        """
        ecmd = array.array('B', struct.pack('I39s', ETHTOOL_GSET, b'\x00' * 39))
        ifreq = struct.pack('16sP', self.name, ecmd.buffer_info()[0])
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)
        # Then modify it to reflect our needs
        ecmd[0:4] = array.array('B', struct.pack('I', ETHTOOL_SSET))

        advertise = 0
        if ten:
            advertise |= ADVERTISED_10baseT_Half | ADVERTISED_10baseT_Full
        if hundred:
            advertise |= ADVERTISED_100baseT_Half | ADVERTISED_100baseT_Full
        if thousand:
            advertise |= ADVERTISED_1000baseT_Half | ADVERTISED_1000baseT_Full

        newmode = struct.unpack('I', ecmd[4:8].tostring())[0] & advertise
        ecmd[8:12] = array.array('B', struct.pack('I', newmode))
        ecmd[18] = 1
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)

    def set_pause_param(self, autoneg, rx_pause, tx_pause):
        """
        Set inter-frame pause
        """
        ecmd = array.array('B', struct.pack('IIII',
                                            ETHTOOL_SPAUSEPARAM, bool(autoneg), bool(rx_pause), bool(tx_pause)))
        buf_addr, _buf_len = ecmd.buffer_info()
        ifreq = struct.pack('16sP', self.name, buf_addr)
        fcntl.ioctl(sockfd, SIOCETHTOOL, ifreq)

    def get_stats(self):
        """
        Get the interface stats
        """
        spl_re = re.compile(br"\s+")

        fp = open(PROCFS_NET_PATH, 'rb')
        # Skip headers
        fp.readline()
        fp.readline()
        while True:
            data = fp.readline()
            if not data:
                return None

            name, stats_str = data.split(b":")
            if name.strip() != self.name:
                continue

            stats = [int(a) for a in spl_re.split(stats_str.strip())]
            break

        titles = ["rx_bytes", "rx_packets", "rx_errs", "rx_drop", "rx_fifo",
                  "rx_frame", "rx_compressed", "rx_multicast", "tx_bytes",
                  "tx_packets", "tx_errs", "tx_drop", "tx_fifo", "tx_colls",
                  "tx_carrier", "tx_compressed"]
        return dict(list(zip(titles, stats)))

    index = property(get_index)
    mac = property(get_mac, set_mac)
    ip = property(get_ip, set_ip)
    netmask = property(get_netmask, set_netmask)


def iterifs(physical=True):
    """
    Iterate over all the interfaces in the system
    """
    net_files = os.listdir(SYSFS_NET_PATH)
    interfaces = set()
    virtual = set()
    for d in net_files:
        path = os.path.join(SYSFS_NET_PATH, d)
        if not os.path.isdir(path):
            continue
        if not os.path.exists(os.path.join(path, b"device")):
            virtual.add(d)
        interfaces.add(d)

    # Some virtual interfaces don't show up in the above search, for example,
    # subinterfaces (e.g. eth0:1). To find those, we have to do an ioctl
    if not physical:
        # ifconfig gets a max of 30 interfaces. Good enough for us too.
        ifreqs = array.array("B", b"\x00" * SIZE_OF_IFREQ * 30)
        buf_addr, _buf_len = ifreqs.buffer_info()
        ifconf = struct.pack("iP", SIZE_OF_IFREQ * 30, buf_addr)
        ifconf_res = fcntl.ioctl(sockfd, SIOCGIFCONF, ifconf)
        ifreqs_len, _ = struct.unpack("iP", ifconf_res)

        assert ifreqs_len % SIZE_OF_IFREQ == 0, (
            "Unexpected amount of data returned from ioctl. "
            "You're probably running on an unexpected architecture")

        res = ifreqs.tostring()
        for i in range(0, ifreqs_len, SIZE_OF_IFREQ):
            d = res[i:i+16].strip(b'\0')
            interfaces.add(d)

    results = interfaces - virtual if physical else interfaces
    for d in results:
        yield Interface(d)


def findif(name, physical=True):
    for br in iterifs(physical):
        if name == br.name:
            return br
    return None


def list_ifs(physical=True):
    """
    Return a list of the names of the interfaces
    """
    return [br for br in iterifs(physical)]


def init():
    """
    Initialize the library
    """
    globals()["sock"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    globals()["sockfd"] = globals()["sock"].fileno()


def shutdown():
    """
    Shutdown the library
    """
    globals()["sock"].close()
    globals()["sock"] = None
    globals()["sockfd"] = None


# Initialize
init()
