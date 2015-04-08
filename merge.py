#!/usr/bin/env python2

"""
This will merge data when all is received

We should be able to handle queries wanting data from one provider as well as multiple.

A query will fill up ``received`` and ``query_sources``. Where ``received`` is
a list of queries we are still waiting for data for, and query_sources is a
hash of sources per query_id, for which we are waiting for data.
"""

# TODO: Do we need both, probably not, as ``received`` contains no more info
# than is provided in ``received``.

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

    # if query_sources is emtpy, this was the last (or only) sender. data
    # should then be merged, and temporary storage should be cleaned. the last
    # step is to send the merged data to the summary server.
    if not query_sources[query_id]:
        merged = merge(received[query_id])
        del received[query_id]
        del query_sources[query_id]
        try:
            urllib2.urlopen("http://localhost:5003/", json.dumps({"query_id": query_id, "data": merged}))
            app.logger.debug("finished %s", merged)
        except urllib2.URLError:
            abort(502)

    app.logger.debug("received: %s, sources left: %s", received.keys(), query_sources)

    return ""


if __name__ == '__main__':
    app.run(port=5002, debug=True)
