#!/usr/bin/env python2

"""This service will serve queries to the registrys"""

import os
import json
from flask import Flask
from flask import abort, jsonify
app = Flask(__name__)

@app.route("/<registry_id>", methods=['GET'])
def serve_registry(registry_id):
    #data = request.get_json(True)
    #registry_id = data['registry_id']
    # the next should de done differently
    query_path = '/tmp/reggy/' + registry_id
    queries = []
    if not os.path.exists(query_path):
        abort(404)
    else:
        with open(query_path, 'r') as f:
            queries = [ json.loads(line) for line in f.readlines() ]
            # TODO: Add timestamp for fetch date, remove or use this timestamp as null
    return jsonify({"queries": queries})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
