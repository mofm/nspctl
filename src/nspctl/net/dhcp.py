import socket
import struct
import logging
import signal
import json
from collections import defaultdict
from time import time

logger = logging.getLogger(__name__)

TYPE_53_DHCPDISCOVER = 1
TYPE_53_DHCPREQUEST = 3


class OutOfLeasesError(Exception):
    pass


class DHCPServer:
    """
    This class implements a DHCP Server
    """

    def __init__(self, **server_settings):

        self.ip = server_settings.get('ip', '172.18.0.1')
        self.port = int(server_settings.get('port', 67))
        self.offer_from = server_settings.get('offer_from', '172.18.0.20')
        self.offer_to = server_settings.get('offer_to', '172.18.0.252')
        self.subnet_mask = server_settings.get('subnet_mask', '255.255.0.0')
        self.router = server_settings.get('router', '172.18.0.1')
        self.dns_server = server_settings.get('dns_server', '172.18.0.1')

        self.broadcast = server_settings.get('broadcast', '')
        if not self.broadcast:
            # calculate the broadcast address from ip and subnet_mask
            nip = struct.unpack('!I', socket.inet_aton(self.ip))[0]
            nmask = struct.unpack('!I', socket.inet_aton(self.subnet_mask))[0]
            nbroadcast = (nip & nmask) | ((~ nmask) & 0xffffffff)
            derived_broadcast = socket.inet_ntoa(struct.pack('!I', nbroadcast))
            self.broadcast = derived_broadcast

        self.static_config = server_settings.get('static_config', dict())
        self.whitelist = server_settings.get('whitelist', False)
        self.save_leases_file = server_settings.get('saveleases', '')
        self.magic = struct.pack('!I', 0x63825363)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(('', self.port))

        # key is MAC
        # separate options dict so we don't have to clean up on export
        self.options = dict()
        self.leases = defaultdict(lambda: {'ip': '', 'expire': 0})
        if self.save_leases_file:
            try:
                leases_file = open(self.save_leases_file, 'rb')
                imported = json.load(leases_file)
                import_safe = dict()
                for lease in imported:
                    packed_mac = struct.pack('BBBBBB', *map(lambda x: int(x, 16), lease.split(':')))
                    import_safe[packed_mac] = imported[lease]
                self.leases.update(import_safe)
                logger.debug('Loaded leases from {0}'.format(self.save_leases_file))
            except IOError:
                pass
            except ValueError:
                pass

        signal.signal(signal.SIGINT, self.export_leases)
        signal.signal(signal.SIGTERM, self.export_leases)
        signal.signal(signal.SIGALRM, self.export_leases)
        signal.signal(signal.SIGHUP, self.export_leases)

    def export_leases(self, signum, frame):
        if self.save_leases_file:
            export_safe = dict()
            for lease in self.leases:
                # translate the key to json safe (and human readable) mac
                export_safe[self.get_mac(lease)] = self.leases[lease]
            leases_file = open(self.save_leases_file, 'wb')
            json.dump(export_safe, leases_file)
            logger.debug('Exported leases to {0}'.format(self.save_leases_file))

        # if keyboard interrupt, propagate upwards
        if signum == signal.SIGINT:
            raise KeyboardInterrupt

    def get_namespaced_static(self, path, fallback=None):
        if fallback is None:
            fallback = {}
        statics = self.static_config
        for child in path.split('.'):
            statics = statics.get(child, {})
        return statics if statics else fallback

    def next_ip(self):
        """
        This method returns the next unleased IP from range
        """
        # if we use ints, we don't have to deal with octet overflow
        # or nested loops (up to 3 with 10/8); convert both to 32-bit integers

        # e.g '192.168.1.1' to 3232235777
        encode = lambda x: struct.unpack('!I', socket.inet_aton(x))[0]

        # e.g 3232235777 to '192.168.1.1'
        decode = lambda x: socket.inet_ntoa(struct.pack('!I', x))
        from_host = encode(self.offer_from)
        to_host = encode(self.offer_to)

        # pull out already leased IPs
        leased = [self.leases[i]['ip'] for i in self.leases
                  if self.leases[i]['expire'] > time()]

        # convert to 32-bit int
        leased = map(encode, leased)

        # loop through, make sure not already leased and not in form X.Y.Z.0
        for offset in range(to_host - from_host):
            if (from_host + offset) % 256 and from_host + offset not in leased:
                return decode(from_host + offset)
        raise OutOfLeasesError('Ran out of IP addresses to lease!')

    def tlv_encode(self, tag, value):
        """
        Encode a TLV option
        """
        if type(value) is str:
            value = value.encode('ascii')
        value = bytes(value)
        return struct.pack('BB', tag, len(value)) + value

    def tlv_parse(self, raw):
        """
        Parse a string of TLV-encoded options
        """
        ret = {}
        while raw:
            [tag] = struct.unpack('B', raw[0:1])
            if tag == 0:  # padding
                raw = raw[1:]
                continue
            if tag == 255:  # end marker
                break
            [length] = struct.unpack('B', raw[1:2])
            value = raw[2:2 + length]
            raw = raw[2 + length:]
            if tag in ret:
                ret[tag].append(value)
            else:
                ret[tag] = [value]
        return ret

    def get_mac(self, mac):
        """
        This method converts the MAC Address
        """
        return ':'.join(map(lambda x: hex(x)[2:].zfill(2), struct.unpack('BBBBBB', mac))).upper()

    def craft_header(self, message):
        """
        This method crafts the DHCP header using parts of the message
        """
        xid, flags, yiaddr, giaddr, chaddr = struct.unpack('!4x4s2x2s4x4s4x4s16s', message[:44])
        client_mac = chaddr[:6]

        # op, htype, hlen, hops, xid
        response = struct.pack('!BBBB4s', 2, 1, 6, 0, xid)
        response += struct.pack('!HHI', 0, 0, 0)

        if self.leases[client_mac]['ip'] and self.leases[client_mac]['expire'] > time():
            offer = self.leases[client_mac]['ip']
        else:  # ACK
            offer = self.get_namespaced_static('dhcp.binding.{0}.ipaddr'.format(self.get_mac(client_mac)))
            offer = offer if offer else self.next_ip()
            self.leases[client_mac]['ip'] = offer
            self.leases[client_mac]['expire'] = time() + 86400

        response += socket.inet_aton(offer)
        response += socket.inet_aton('0.0.0.0')
        response += socket.inet_aton('0.0.0.0')
        response += chaddr

        # BOOTP legacy pad
        response += b'\x00' * 64
        response += b'\x00' * 128
        response += self.magic
        return client_mac, response

    def craft_options(self, opt53, client_mac):
        """
        This method crafts the DHCP option fields
        """
        response = self.tlv_encode(53, struct.pack('!B', opt53))
        response += self.tlv_encode(54, socket.inet_aton(self.ip))

        subnet_mask = self.get_namespaced_static('dhcp.binding.{0}.subnet'.format(self.get_mac(client_mac)),
                                                 self.subnet_mask)
        response += self.tlv_encode(1, socket.inet_aton(subnet_mask))
        bcast_addr = self.get_namespaced_static('dhcp.binding.{0}.router'.format(self.get_mac(client_mac)),
                                                self.broadcast)
        response += self.tlv_encode(28, socket.inet_aton(bcast_addr))
        router = self.get_namespaced_static('dhcp.binding.{0}.router'.format(self.get_mac(client_mac)), self.router)
        response += self.tlv_encode(3, socket.inet_aton(router))
        dns_server = self.get_namespaced_static('dhcp.binding.{0}.dns'.format(self.get_mac(client_mac)),
                                                [self.dns_server])
        dns_server = b''.join([socket.inet_aton(i) for i in dns_server])
        response += self.tlv_encode(6, dns_server)
        response += self.tlv_encode(51, struct.pack('!I', 86400))

        response += b'\xff'
        return response

    def dhcp_offer(self, message):
        """
        This method responds to DHCP discovery with offer
        """
        client_mac, header_response = self.craft_header(message)
        options_response = self.craft_options(2, client_mac)
        response = header_response + options_response

        self.sock.sendto(response, (self.broadcast, 68))

    def dhcp_ack(self, message):
        """
        This method responds to DHCP request with acknowledge
        """
        client_mac, header_response = self.craft_header(message)
        options_response = self.craft_options(5, client_mac)
        response = header_response + options_response

        self.sock.sendto(response, (self.broadcast, 68))

    def validate_req(self, client_mac):
        """
        Client request is valid only
        """
        if self.whitelist and self.get_mac(client_mac) not in self.get_namespaced_static('dhcp.binding'):
            logger.debug('Non-whitelisted client request received from {0}'.format(self.get_mac(client_mac)))
            return False
        if 60 in self.options[client_mac]:
            logger.debug('client request received from {0}'.format(self.get_mac(client_mac)))
            return True
        logger.error('Blocked non-whitelisted client request received from {0}'.format(self.get_mac(client_mac)))
        return False

    def listen(self):
        """
        Main listen method
        """
        while True:
            message, address = self.sock.recvfrom(1024)
            [client_mac] = struct.unpack('!28x6s', message[:34])
            self.options[client_mac] = self.tlv_parse(message[240:])

            if not self.validate_req(client_mac):
                pass
            dhtype = ord(self.options[client_mac][53][0])
            if dhtype == TYPE_53_DHCPDISCOVER:
                logger.debug('Sending DHCPOFFER to {0}'.format(self.get_mac(client_mac)))
                try:
                    self.dhcp_offer(message)
                except OutOfLeasesError:
                    logger.critical('Ran out of leases')
            elif dhtype == TYPE_53_DHCPREQUEST:
                logger.debug('Sending DHCPACK to {0}'.format(self.get_mac(client_mac)))
                self.dhcp_ack(message)
            else:
                logger.debug('Unhandled DHCP message type {0} from {1}'.format(dhtype, self.get_mac(client_mac)))
