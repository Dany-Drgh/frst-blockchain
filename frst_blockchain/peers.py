import asyncio
from cgitb import handler
from http import server
from venv import create

import structlog
from frst_blockchain.messages import(
    create_peers_message,
    create_block_message,
    create_transaction_message,
    create_ping_message
)
from frst_blockchain.transactions import validate_transaction

logger = structlog.getLogger(__name__)

class P2PError(Exception):
    pass

class P2PProtocol():
    def __init__(self, server):
        self.server = server
        self.blockchain = server.blockchain
        self.connection_pool = server.connection_pool

    @staticmethod
    async def send_message(writer, message):
        # Sends mesage to specific peer, (writer)
        writer.write(message.encode + b"\n")

    async def handle_message(self, message, writer):
        # Handles incoming message passed by server
        # Hands mesage off to more specific method 
        message_handlers = {
            "block" : self.handle_block,
            "ping" : self.handle_ping,
            "peers" : self.handle_peers,
            "transaction" : self.handle_transaction 
        }

        handler = message_handlers.get(message["name"])
        if not handler:
            raise ("Missing handler for message")

        await handler(message)

    async def handle_ping(self, message, writer):
        # Handles incoming "ping" message
        block_height = message["payload"]["block_height"]

        # If writer is miner he is marked as such
        writer.is_miner = message["payload"]["is_miner"]

        # Send the 20 most active peers to user 
        peers = self.connection_pool.get_peers(20)
        peers_message = create_peers_message(self.server.external_ip, self.server.external_port, peers)
        await self.send_message(writer, peers_message)
        
        # Send blocks to peers if they have less than user
        if block_height < self.blockchain.last_block["height"]:
            for block in self.blockchain.chain[block_height+1]:
                await self.send_message(
                    writer,
                    create_block_message(
                        self.server.external_ip,
                        self.server.external_port,
                        block
                    )
                )

    async def handle_transaction(self, message, writer):
        # Handles incoming "transaction" message
        logger.info("Recieved transaction")

        # Validate transaction
        tx = message["payload"]

        if validate_transaction(tx) is True:
            # Add tx to transaction list and propagate
            if tx not in self.blockchain.transactions:
                self.blockchain.pending_transactions.append(tx)

                for peer in self.connection_pool.get_alive_peers(20):
                    await self.send_message(
                        peer,
                        create_transaction_message(
                            self.server.external_ip,
                            self.server.external_port,
                            tx
                        )
                    )
            else:
                logger.warning("Recieved invalid transaction")        

    async def handle_block(self, message, writer):
        # Handles incoming "block" message
        logger.info("Recieved new block")

        block = message["payload"]

        # Add block to blockchain if valid
        self.blockchain.add_block(block)

        # Propagate block to peers
        for peer in self.connection_pool.get_alive_peers(20):
            await self.send_message(
                peer,
                create_block_message(
                    self.server.external_ip, self.server.external_port, block
                )
            )


    async def handle_peers(self, message, writer):
        # Handles incoming "peers" message
        logger.info("Recieved new peers")

        peers = message["payload"]

        # Generate ping message to send to other peers
        ping_message = create_ping_message(
            self.server.external_ip,
            self.server.external_port,
            len(self.blockchain.chain),
            len(self.server.connection_pool.get_alive_peers(50)),
            False,
        )

        for peer in peers:
            # Try to connect and add to pool is successfull
            reader, writer = await asyncio.open_connection(peer["ip"],peer["port"])

            self.connection_pool.add_peer(writer)

            await self.send_message(writer, ping_message)

