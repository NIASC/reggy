#!/usr/bin/env python3

"""
This service will serve queries to the registrys. Queries are fetched from
one or more frontend servers having a web interface or similar.

The queries are saved and cached in the query server with info about who has
already signed it. This list is compared at registries to decide if the query
should be verified and processed.

Registry servers sends one type of request, and get a combined result back from
the query server, which will be a subset of this query cache, with the queries
relevant for this registry. The registry get a limited time to sign queries and
return. During that time, signing is blocked for other registries.
"""

import os
import json
import gnupg
import logging
import socketserver
from urllib import request

from lib import get_config, encrypt, decrypt

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('query')

config = get_config()
# get encryption config from config file
# keydir could be null in the file to use the default key folder
encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'

cached_queries = {}


def fetch_queries(registry_id):
    data = request.urlopen("http://localhost:5000/queries").read()
    logger.debug("all queries %s", data.decode("utf-8"))
    queries = json.loads(data.decode("utf-8"))
    filtered = []
    for query in queries['queries']:
        # fill local cache
        query_id = query.get('id')
        if query_id not in cached_queries:
            query['signed_by'] = []
            original = json.dumps(query['fields'])
            signed = gpg.sign(original)
            query['signed'] = signed.data.decode("utf-8")
            cached_queries[query_id] = query

    for query_id, query in cached_queries.items():
        if registry_id in query['sources']:
            # earlier, we picked out the relevant part, but we now let the
            # registries do that themselves
            filtered.append(query)
    queries = {"queries": filtered}
    logger.debug("filtered    %s", queries)
    return queries


class QueryHandler(socketserver.StreamRequestHandler):

    def handle(self):
        self.data = self.rfile.readline().strip()
        data = json.loads(self.data.decode("utf-8"))

        # TODO: Create good filter
        # TODO: Source ID should be replaced by mapping to IP/PORT for registries
        if 'source_id' in data and data['source_id'] in ['hunt', 'cancer']:
            queries = fetch_queries(data['source_id'])

            encrypted = encrypt(queries, "sigurdga@edge")

            logger.info("sending     %s", encrypted)
            self.request.sendall(encrypted + bytes("\n", "utf-8"))

            received = self.rfile.readline().strip()
            logger.debug("received  %s", received)

            signed_queries = decrypt(received)

            logger.debug("decrypted_data %s", signed_queries)
            # reset timeout lock
            for query_id, query in signed_queries.items():
                # verify
                verified = gpg.verify(query)
                if not verified:
                    raise ValueError(
                        "Signature could not be verified for query_id %s",
                        query_id)

                # update cached_queries
                cached_queries[query_id]['signed_by'].append(data['source_id'])
                cached_queries[query_id]['signed'] = query

            logger.debug(cached_queries)


if __name__ == "__main__":
    HOST, PORT = "localhost", 50010

    server = socketserver.TCPServer((HOST, PORT), QueryHandler)
    server.serve_forever()
