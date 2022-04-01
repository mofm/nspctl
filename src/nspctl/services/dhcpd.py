from ..lib.daemon import Daemon
from ..net.dhcp import DHCPServer


class DHCPService(Daemon):
    """
    DHCPServer run method class
    """
    def run(self):
        dserv = DHCPServer()
        dserv.listen()


dhdaemon = DHCPService()


def dhcp_start():
    """
    DHCP Service start function
    """
    return dhdaemon.start()


def dhcp_stop():
    """
    DHCP service stop function
    """
    return dhdaemon.stop()


def dhcp_reload():
    """
    DHCP Service reload function
    """
    return dhdaemon.reload()


def dhcp_status():
    """
    DHCP service status function
    """
    return dhdaemon.status()
