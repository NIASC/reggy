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

import json
import logging
import socketserver
from urllib import request

import config
from lib import sign, verify
from lib import serialize_encrypt_and_encode, decode_decrypt_and_deserialize

logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('query')

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
            signed = sign(original)
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
        # TODO: Source ID should be replaced by mapping to IP/PORT
        valid_sources = ['hunt', 'cancer', 'death']
        if 'source_id' in data and data['source_id'] in valid_sources:
            queries = fetch_queries(data['source_id'])

            if not config.RECIPIENTS[data['source_id']]:
                raise Exception("Could not find encryption config for %s", data['source_id'])

            encrypted = serialize_encrypt_and_encode(
                queries, config.RECIPIENTS[data['source_id']])

            logger.info("sending     %s", encrypted)
            self.request.sendall(encrypted + bytes("\n", "utf-8"))

            received = self.rfile.readline().strip()
            logger.debug("received  %s", received)

            signed_queries = decode_decrypt_and_deserialize(received)

            logger.debug("decrypted_data %s", signed_queries)
            # reset timeout lock
            for query_id, query in signed_queries.items():
                # verify
                verified = verify(query)
                if not verified:
                    raise ValueError(
                        "Signature could not be verified for query_id %s",
                        query_id)

                # update cached_queries
                cached_queries[query_id]['signed_by'].append(data['source_id'])
                cached_queries[query_id]['signed'] = query

            logger.debug(cached_queries)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    )
    server = socketserver.TCPServer((config.QUERY_SERVER_HOST,
                                     config.QUERY_SERVER_PORT),
                                    QueryHandler)
    server.serve_forever()
