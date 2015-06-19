#!/usr/bin/env python3

"""This service will serve queries to the registrys"""

import os
import json
import logging
import socketserver
from urllib import request

from lib import encrypt

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('query')

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'config.json')

try:
    config = json.load(open(configfile))
except IOError:
    logger.warning('Config file not found, using defaults')
    config = {}


def fetch_queries(registry_id):
    data = request.urlopen("http://localhost:5000/queries").read()
    logger.debug("all queries %s", data.decode("utf-8"))
    queries = json.loads(data.decode("utf-8"))
    filtered = []
    for query in queries['queries']:
        if registry_id in query['sources']:
            query['fields'] = query[registry_id]
            filtered.append(query)
    queries = {"queries": filtered}
    logger.debug("filtered    %s", queries)
    return queries


class QueryHandler(socketserver.StreamRequestHandler):

    def handle(self):
        self.data = self.rfile.readline().strip()
        data = json.loads(self.data.decode("utf-8"))

        # TODO: Create good filter
        if 'source_id' in data and data['source_id'] in ['hunt', 'cancer']:
            queries = fetch_queries(data['source_id'])

            encrypted = encrypt(queries, "sigurdga@edge")

            logger.info("sending     %s", encrypted)
            self.request.sendall(encrypted + bytes("\n", "utf-8"))


if __name__ == "__main__":
    HOST, PORT = "localhost", 50010

    server = socketserver.TCPServer((HOST, PORT), QueryHandler)
    server.serve_forever()
