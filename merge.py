#!/usr/bin/env python3

"""
This will merge data when all is received

We should be able to handle queries wanting data from one provider as well as
multiple.

A query will fill up ``received`` and ``query_sources``. Where ``received`` is
a list of queries we are still waiting for data for, and query_sources is a
hash of sources per query_id, for which we are waiting for data.
"""

# TODO: Do we need both, probably not, as ``received`` contains no more info
# than is provided in ``received``.

import logging
import socketserver

from lib import get_config
from lib import decode_decrypt_and_deserialize, serialize_encrypt_and_send

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('merge')

received = {}
query_sources = {}

config = get_config()


def merge(data):
    """
    Data is a dict of source ids and a new dict. The inner dict consists of
    hashed ids and encrypted data per person.

    We return merged data in a dict where the hashed id is the key.
    """
    total = []
    registries = list(data)
    logger.debug("Merging data from sources: %s", ", ".join(registries))
    if registries:  # We have something to do
        for hashed_id in data[registries[0]]:
            in_all = True
            merged_data = {}
            # doing all as this is faster than looping twice
            for registry in registries:
                if hashed_id not in data[registry]:
                    in_all = False
                    break
                merged_data[registry] = data[registry][hashed_id]
            if in_all:
                total.append(list(merged_data.values()))
    return total


class MergeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decode_decrypt_and_deserialize(self.data)

        query_id = data['query_id']
        source_id = data['source_id']
        sources = data['sources']

        # first dataset using a query_id will set the acceptable sources
        if query_id not in query_sources:
            query_sources[query_id] = sources

        logger.debug("Got data from %s, while waiting for data from: %s",
                     source_id, ", ".join(query_sources[query_id]))
        if source_id not in query_sources[query_id]:
            # this is wrongly sent data. Exit with bad_request
            # this should be unnecessary
            # TODO: Cancel by sending nothing and handle that later
            logger.error("Source %s not expected to send data for query %s",
                         source_id, query_id)
            response = ""
            self.request.sendall(bytes(response, "utf-8"))
            return

        if query_id not in received:
            received[query_id] = {}

        # if accepted by registry make data ready to merge
        if 'data' in data:
            received[query_id][source_id] = data['data']

        logger.debug("Will remove %s from remaining sources for query %s",
                     source_id, query_id)
        query_sources[query_id].remove(source_id)

        # if query_sources is empty, this was the last (or only) sender. Data
        # should then be merged, and temporary storage should be cleaned. The
        # last step is to send the merged data to the summary server.
        if not query_sources[query_id]:
            merged = merge(received[query_id])
            logger.debug("Merged %s", data)
            logger.debug("Merged to %s", merged)
            logger.debug("Removing data for query id %s", query_id)
            del received[query_id]
            logger.debug("Removing query %s from query sources", query_id)
            del query_sources[query_id]
            data = {"query_id": query_id, "data": merged}
            serialize_encrypt_and_send(data,
                                       "sigurdga@edge",
                                       config['summary_server_port'])

        logger.debug("Sources left per query: %s", query_sources)

        response = ""
        self.request.sendall(bytes(response, "utf-8"))


if __name__ == '__main__':
    HOST, PORT = "localhost", 50020

    server = socketserver.TCPServer((HOST, PORT), MergeHandler)
    server.serve_forever()
