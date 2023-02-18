import hashlib
import json
import time
from flask import Flask, jsonify, request
import requests


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hash_string = str(self.index) + str(self.timestamp) + str(self.data) + str(self.previous_hash)
        return hashlib.sha256(hash_string.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True


# Instantiate our Node
app = Flask(__name__)

# Instantiate the Blockchain
blockchain = Blockchain()

# Store the address of nodes connected to the network
peer_nodes = set()


@app.route('/new_block', methods=['POST'])
def new_block():
    data = request.get_json()
    block = Block(data['index'], data['timestamp'], data['data'], data['previous_hash'])
    blockchain.add_block(block)
    response = {'message': 'Block added successfully'}
    return jsonify(response), 201


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': [vars(block) for block in blockchain.chain],
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/add_nodes', methods=['POST'])
def add_nodes():
    nodes = request.get_json()
    if not nodes:
        return 'No nodes', 400
    for node in nodes:
        peer_nodes.add(node)
    response = {'message': 'Nodes added successfully',
                'total_nodes': list(peer_nodes)}
    return jsonify(response), 201


# Consensus Algorithm
def consensus():
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)
    for node in peer_nodes:
        response = requests.get(f'http://{node}/get_chain')
        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']
            if length > current_len and blockchain.is_chain_valid(chain):
                current_len = length
                longest_chain = chain
    if longest_chain:
        blockchain = longest_chain
        return True
    return False


@app.route('/consensus', methods=['GET'])
def request_consensus():
    if consensus():
        response = {'message': 'Blockchain replaced'}
    else:
        response = {'message': 'No consensus required'}
    return jsonify(response), 200


# Running the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
