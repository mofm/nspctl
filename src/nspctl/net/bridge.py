import array
import fcntl
import os
import struct

from . import netbase

SYSFS_NET_PATH = b"/sys/class/net"

# From linux/sockios.h
SIOCBRADDBR = 0x89a0
SIOCBRDELBR = 0x89a1
SIOCBRADDIF = 0x89a2
SIOCBRDELIF = 0x89a3

SIOCDEVPRIVATE = 0x89F0

# From bridge-utils if_bridge.h
BRCTL_SET_BRIDGE_FORWARD_DELAY = 8

if not os.path.isdir(SYSFS_NET_PATH):
    raise Exception("'{}': path not found".format(SYSFS_NET_PATH))


class Bridge(netbase.Interface):
    """
    Common class for Linux network bridge interface
    """

    def __init__(self, name):
        netbase.Interface.__init__(self, name)

    def iterifs(self):
        """
        Iterate over all the interfaces in this bridge
        """
        if_path = os.path.join(SYSFS_NET_PATH, self.name, b"brif")
        net_files = os.listdir(if_path)
        for iface in net_files:
            yield iface

    def listif(self):
        """
        List interface names
        """
        return [p for p in self.iterifs()]

    def addif(self, iface):
        """
        Add the interface with the given name to this bridge
        """
        if type(iface) == netbase.Interface:
            devindex = iface.index
        else:
            devindex = netbase.Interface(iface).index
        ifreq = struct.pack('16si', self.name, devindex)
        fcntl.ioctl(netbase.sockfd, SIOCBRADDIF, ifreq)
        return self

    def delif(self, iface):
        """
        Remove the interface with the given name from this bridge
        """
        if type(iface) == netbase.Interface:
            devindex = iface.index
        else:
            devindex = netbase.Interface(iface).index
        ifreq = struct.pack('16si', self.name, devindex)
        fcntl.ioctl(netbase.sockfd, SIOCBRDELIF, ifreq)
        return self

    def set_forward_delay(self, delay):
        """
        Delay is passed to kernel
        """
        data = array.array('L', [BRCTL_SET_BRIDGE_FORWARD_DELAY, int(delay * 100), 0, 0])
        buffer, _items = data.buffer_info()
        ifreq = struct.pack('16sP', self.name, buffer)
        fcntl.ioctl(netbase.sockfd, SIOCDEVPRIVATE, ifreq)
        return self

    def delete(self):
        """
        Remove the bridge interface
        """
        self.down()
        fcntl.ioctl(netbase.sockfd, SIOCBRDELBR, self.name)
        return self

    def get_ip(self):
        """
        Return IP address of bridge
        """
        return "0.0.0.0"

    ip = property(get_ip)


def shutdown():
    """
    Shut down bridge lib
    """
    netbase.shutdown()


def iterbridges():
    """
    Iterate over all the bridges in the system
    """
    net_files = os.listdir(SYSFS_NET_PATH)
    for d in net_files:
        path = os.path.join(SYSFS_NET_PATH, d)
        if not os.path.isdir(path):
            continue
        if os.path.exists(os.path.join(path, b"bridge")):
            yield Bridge(d)


def list_bridges():
    """
    Return a list of the names of the bridge interfaces
    """
    return [br for br in iterbridges()]


def addbr(name):
    """
    Create new bridge with the given name
    """
    fcntl.ioctl(netbase.sockfd, SIOCBRADDBR, name)
    ifc = netbase.Interface(name)
    if not ifc.is_up():
        ifc.up()
    return Bridge(name)


def findif(name):
    """
    Find the given interface name within any of the bridges
    """
    for br in iterbridges():
        if name in br.iterifs():
            return br
    return None


def findbridge(name):
    """
    Find the given bridge
    """
    for br in iterbridges():
        if br.name == name:
            return br
    return None
