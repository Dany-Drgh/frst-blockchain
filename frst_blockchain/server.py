import asyncio
from asyncio import IncompleteReadError, StreamReader, StreamWriter
from asyncio.log import logger

import structlog
from marshmallow.exceptions import MarshmallowError

from frst_blockchain.messages import BaseSchema
from frst_blockchain.utils import get_external_ip

logger = structlog.getlogger()


class Server:
    def __init__(self, blockchain, connection_pool, p2p_protocol):
        self.blockchain = blockchain
        self.connection_pool = connection_pool
        self.p2pprotocol = p2p_protocol
        self.external_ip = None
        self.external_port = None

        if not (blockchain, connection_pool, p2p_protocol):
            logger.error("'blockchain', 'connection_pool', and 'gossip_protocol' must all be instantiated")
            raise Exception("Could not start")
    
    async def get_external_ip(self):
        #Finds our "external IP"
        self.external_ip = await get_external_ip()

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter):
        # This function is called when we receive a new connection
        # The `writer` object represents the connecting peer
        while True:
            try:
                # Handling and/or replying to the incoming data
                data = await reader.readuntil(b"\n")
                
                decoded_data = data.decode("utf-8").strip()
            
                try:
                    message = BaseSchema().loads(decoded_data)


                except(asyncio.exceptions.IncompleteReadError,ConnectionError):
                    # An error happened, break out of the wait loop
                    break

                # Extract the address from the message, add it to the writer object 
                writer.address = message["meta"]["address"]

                # Adding peer to peer connection
                self.connection_pool.add_peer(writer)

                # Handling the message
                await self.p2p_protocol.handle_message(message, writer)

                await writer.drain()
                if writer.is_closing():
                    break

            except (asyncio.exceptions.IncompleteReadError, ConnectionError):
                # An error happened, break out of the wait loop
                    break
        
        # Cleaning up after connection
        writer.close()
        await writer.wait_closed()
        self.connection_pool.remove_peer(writer)           
    
    async def listen(self, hostname="0.0.0.0", port=8888):
        # This is the listen method which spawns our server
        server = await asyncio.start_server(self.handle_connection, hostname, port)
        logger.info(f"Server listening on {hostname}:{port}")

        self.external_ip = await self.get_external_ip()
        self.external_port = 8888

        async with server:
            await server.serve_forever()    