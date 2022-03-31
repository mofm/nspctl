from ..net import netbase
from ..net.bridge import addbr, findbridge


# convert string to bytes
BRNAME = "nspctl0".encode()
NEWIP = "172.18.0.1"
NETMASK = 16


def createbridge():
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
    netbase.shutdown()
