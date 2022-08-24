from http import server
from frst_blockchain.blockchain import Blockchain
from frst_blockchain.connections import ConnectionPool
from frst_blockchain.peers import P2PProtocol
from frst_blockchain.server import Server

blockchain = Blockchain()
connection_pool = ConnectionPool()

server = Server(blockchain, connection_pool, P2PProtocol)

async def main():
    await server.listen()

asyncio.run(main())