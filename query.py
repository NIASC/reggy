#!/usr/bin/env python2

"""This service will serve queries to the registrys"""

import json
import urllib2
from flask import Flask
from flask import jsonify
app = Flask(__name__)

@app.route("/<registry_id>", methods=['GET'])
def serve_registry(registry_id):
    data = urllib2.urlopen("http://localhost:5000/queries").read()
    queries = json.loads(data)
    filtered = []
    for query in queries['queries']:
        if registry_id in query['sources']:
            query['fields'] = query[registry_id]
            filtered.append(query)
    return jsonify({"queries": filtered})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
