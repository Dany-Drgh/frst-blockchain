import hashlib
import json
from time import time
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
                length = resposne.json()['length']
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
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'nonce': None,
        }
        # Get the hash of this new block, and add it to the block
        block_hash = self.hash(block)
        block["hash"] = block_hash

        # Resetting current transaction lists
        self.current_transactions = []

        self.chain.append(block)
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

    def proof_of_work(self, last_proof):
        # Simple Proof of Work Algorithm:
        #  - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
        #  - p is the previous proof, and p' is the new proof

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof


    @staticmethod
    def valid_proof(last_proof, proof):

        # Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

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

