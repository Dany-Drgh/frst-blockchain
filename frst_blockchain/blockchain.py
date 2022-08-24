import asyncio
from asyncio.log import logger
import json
import math
import random
from hashlib import sha256
from time import time

import structlog

logger = structlog.getlogger("blockchain")

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.target = "0000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        # Create the genesis block
        logger.info("Creating Genesis block.")
        self.chain.append(self.new_block())


    def new_block(self):
        # Create a new Block in the Blockchain
        # proof: <int> The proof given by the Proof of Work algorithm
        # previous_hash: (Optional) <str> Hash of previous Block
        # return: <dict> New Block
        block = {
            'height': len(self.chain) + 1,
            'transactions': self.pending_transactions,
            'previous_hash': self.last_block["hash"] if self.last_block else None,
            'nonce': format(random.getrandbits(64), "x"),
            'target' : self.target,
            'timestamp': time(),
        }

        # Resetting current transaction lists
        self.pending_transactions = []
        return block        

    @staticmethod
    def create_block(height, transactions, previous_hash, nonce, target, timestamp=None):
        block = {
            "height": height,
            "transactions": transactions,
            "previous_hash": previous_hash,
            "nonce": nonce,
            "target": target,
            "timestamp": timestamp or time(),
        }
        
        # Get the hash of this new block, and add it to the block
        block_string = json.dumps(block, sort_keys=True).encode()
        block["hash"] = sha256(block_string).hexdigest()
        
        return block

    @staticmethod 
    def hash(block):
        # Hashes a Block with SHA-256
        # Dictionary has to be Ordered or  have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns last Block of the blockchain
        return self.chain[-1] if self.chain else None

    @staticmethod
    def valid_block(self, block):
        # Validates the Proof: Does hash(block) start with 4 zeroes?
        return block['hash']< self.target

    def add_block(self, block):
        # /!\ TO DO: Add proper validation logic here /!\
        self.chain.append(block)

    def recalculate_target(self, block_index):
        # Retruns the number we need to get below to to mine a block   

        #Check if recalculation is needed:
        if block_index % 10 == 0:
            # Expected timespan of 10 blocks
            expected_timespan = 10*10 

            # Calculate actual time span
            actual_timespan = self.chain[-1]["timepstamp"]- self.chain[-10]["timestamp"]

            # Calculate and ajust offset
            ratio = actual_timespan/expected_timespan
            ratio = max(0.25, ratio)
            ratio = min(4.00, ratio)

            # Calculate new target by multiplying current one by ratio
            new_target = int(self.target, 16) * ratio

            self.target = format(math.floor(new_target), "x").zfill(64)
            logger.info(f"Calculated new mining target:{self.target}")
            return self.target

    async def get_blocks_after_timestamp(self, timestamp):
        for index, block in enumerate(self.chain):
            if timestamp < block["timestamp"]:
                return self.chain[index:]

    async def mine_new_block(self):
        self.recalculate_target(self.last_block["index"] + 1 )
        while True:
            new_block = self.new_block()
            if self.valid_block(new_block):
                break
                
                await asyncio.sleep(0)

        self.chain.append(new_block)
        logger.info(f"Found a new block: {new_block}")

        

    



