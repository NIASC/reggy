#!/usr/bin/env python2

"""
This will merge data when all is received
"""

import json
import urllib2
from flask import Flask
from flask import request, abort
app = Flask(__name__)

received = {}
query_sources = {}

def merge(lists):
    total = {}
    registrys = lists.keys()
    for id in lists[registrys[0]]:
        in_all = True
        data = {}
        for registry in registrys:  # doing all as this is faster than looping twice
            if id not in lists[registry]:
                in_all = False
                break
            data[registry] = lists[registry][id]
        if in_all:
            total[id] = data
    return total


@app.route("/", methods=['POST'])
def receive_data():
    data = request.get_json(True)
    query_id = data['query_id']
    source_id = data['source_id']
    sources = data['sources']

    # first dataset using a query_id will set the acceptable sources
    if not query_id in query_sources:
        query_sources[query_id] = sources

    if not unicode(source_id) in query_sources[query_id]:
        # this is wrongly sent data. exit with bad_request
        # this should be unnecessary
        abort(400)

    if not query_id in received:
        received[query_id] = {}

    received[query_id][source_id] = data['data']
    query_sources[query_id].remove(source_id)

    # query_sources may be empty if this is the data sender
    if not query_sources[query_id]:
        # TODO: Do more than just print
        merged = merge(received[query_id])
        urllib2.urlopen("http://localhost:5003/", json.dumps({"query_id": query_id, "data": merged}))
        print "finished", merged
        del received[query_id]
        del query_sources[query_id]

    print received.keys(), query_sources

    return ""


if __name__ == '__main__':
    app.run(port=5002, debug=True)
