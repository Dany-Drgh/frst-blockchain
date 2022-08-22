from blockchain import Blockchain
from uuid import uuid4
from flask import Flask, jsonify, request


# Node creation
app = Flask(__name__)

# Generate a unique address for the node
node_identifier = str(uuid4()).replace('-','')

# Blockchain instantiation
blockchain = Blockchain()

# mine endpoint creation
@app.route('/mine', methods=['GET'])
def mine():
    # Running proof of work algorithm to get new proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Rewarding miner, sender '0' means coin earned from mining
    blockchain.new_transaction(
        sender = '0',
        recipient = node_identifier,
        amount = 1,
    )    
    
    # Forging new block by adding it to chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message' : "New Block is forged",
        'hash':block['hash'],
        'index' : block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

# new transaction endpoint creation
@app.route("/transaction/new",methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check completeness of POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return "Missing Values", 400

    # Create new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response= {'message':f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

# chain endpoint creation
@app.route("/chain", methods=["GET"])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


# Neighboring nodes adding endpoint
@app.route("/nodes/register", methods=["POST"])
def register_nodes():

    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please enter valid list of nodes", 400
    
    for node in nodes :
        blockchain.register_node(node)

    response = {
        'message': 'New nodes added',
        'total_nodes': list(blockchain.nodes) 
    }
    return jsonify(response), 200

# Conflict resolution algorithm
@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response={
            'message':'Current chain has been replaced',
            'chain':blockchain.chain
        }
    else:
        response={
            'message':'Current chain is authoritative',
            'chain':blockchain.chain
        }
    return jsonify(response),200 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


    
        