from asyncio.log import logger
from ipaddress import ip_address
import structlog
from more_itertools import take

logger = structlog.getLogger(__name__)

class ConnectionPool:
    def __init__(self):
        self.connection_pool = dict()

    def broadcast(self, message):
        for user in self.connection_pool:
            user.write(f"{meesage}".encode())

    @staticmethod
    def get_address_string(writer):
        # Get a peer's ip:port (address)
        ip = writer.address["ip"]
        port = writer.address["port"]
        return f"{ip}:{port}"

    def add_peer(self, writer):
        address = self.get_address_string(writer)
        self.connection_pool[address] = writer
        logger.info("Added new peer to pool", address = address)

    def remove_peer(self, writer):
        address = self.get_address_string(writer)
        self.connection_pool.pop(address)
        logger.info("Removed peer from pool", address = address)

    def get_alive_peer(self):
        # Return SOME connected peers
        # TO DO : Sort by most active
        return take(count, self.connection_pool.items())
