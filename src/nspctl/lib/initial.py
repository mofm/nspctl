from ..net import netbase
from ..net.bridge import addbr, findbridge
from ..utils.sysctl import lsmod, modprobe, sysctlset
from ..services.dhcpd import dhcp_start


# convert string to bytes
BRNAME = "nspctl0".encode()
NEWIP = "172.18.0.1"
NETMASK = 16
KMODULES = ["br_netfilter", ]
SYSSETS = {"net.ipv4.ip_forward": 1, }


def initialbridge():
    """
    Initialize the bridge interface
    """

    if not findbridge(BRNAME):
        addbr(BRNAME)
    else:
        raise Exception("bridge interface already exists: '{}'".format(BRNAME))

    brint = netbase.Interface(BRNAME)
    # add new ip address to interface
    brint.set_ip(NEWIP)
    # set new netmask
    brint.set_netmask(NETMASK)
    # shutdown netbase library
    netbase.shutdown()


def initialsys():
    """
    Initial system wide configuration
    """
    mods = lsmod()
    for i in KMODULES:
        if i not in mods:
            modprobe(i)

    # set sysctl configuration
    for k, v in SYSSETS.items():
        sysctlset(k, v)


def initialize():
    """
    Main startup initialization function
    """
    try:
        initialbridge()
        initialsys()
        dhcp_start()
    except Exception as exc:
        raise Exception("Initialization failed: {}".format(exc))
