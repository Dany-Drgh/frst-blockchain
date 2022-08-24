import hashlib
import json
from random import random
from time import datetime
from urllib import request
from urllib.parse import urlparse


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.new_block(proof= 100, previous_hash=1)
    
    def register_node (self, address):
        #Add new node to list of nodes
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def valid_node (self, chain):
        # Check given blockchain validity
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n--------------------\n")

            # Check that hash is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            
            # Check that P.O.W. is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        # Consensus algorithm, resolves conflicts by replacing all chains with longest valid one
        # returns True if chain replaced False if not 
        neighbors = self.nodes
        new_chain = None

        max_length = len(self.chain) # Longest known length of chain

        # Check all chains from neighbors
        for node in neighbors:
            response = request.get(f'http://{node}/chain')
        
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

            # Compare chains lengths and check for validity
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain
        
        # If new chain is found replace old one 
        if new_chain:
            self.chain = new_chain
            return True
        
        return False

    def new_block(self, proof, previous_hash=None):
        # Create a new Block in the Blockchain
        # proof: <int> The proof given by the Proof of Work algorithm
        # previous_hash: (Optional) <str> Hash of previous Block
        # return: <dict> New Block
        block = {
            'index': len(self.chain) + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'transactions': self.current_transactions,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'nonce': format(random.getrandbits(64), "x"),
        }
        # Get the hash of this new block, and add it to the block
        block_hash = self.hash(block)
        block["hash"] = block_hash

        # Resetting current transaction lists
        self.current_transactions = []
        return block        

    def new_transaction(self, sender, recipient, amount ):
        # Creates a new transaction to go into the next mined Block
        # :return: <int> The index of the Block that will hold this transaction
        self.current_transactions.append({
            'sender': sender,
            'recipient' : recipient,
            'amount' : amount
        } )

        return self.last_block['index']+1

    def proof_of_work(self):
        # Simple Proof of Work Algorithm:
        # New block is created if block's hash starts with '0000' block is added to the chain
        # If block is not valid try again.
        # return valid block's nonce
        while True:
            new_block = self.new_block()
            if self.valid_block(new_block):
                break 
        self.chain.append(new_block)
        return new_block['nonce']


    @staticmethod
    def valid_block(block):
        # Validates the Proof: Does hash(block) start with 4 zeroes?
        return block['hash'].startswith('0000')

    @staticmethod 
    def hash(block):
        # Hashes a Block with SHA-256
        # Dictionary has to be Ordered or  have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns last Block of the blockchain
        return self.chain[-1]

