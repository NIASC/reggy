#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import os
import gnupg
import json
import logging
import socketserver

logger = logging.getLogger(__name__)

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
try:
    config = json.load(open(configfile))
except IOError:
    logger.info('Config file not found, using defaults')
    config = {}

# TODO: Add a layer between this and merge, do decrypt data from merge

# TODO: The new layer could also do "project" or "select" on the returned data

# TODO: Put path to summarize server public key in config file

encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


class SummaryHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().split()
        print(self.data)
        data = json.loads(self.data.decode("utf-8"))
        print(data)

        logger.debug("got %s", data)

        if encryption_config.get('encrypt_data', True):
            results = {}
            # decrypt
            for id, result in data["data"].items():
                results[id] = {}
                for source_id, encrypted in result.items():
                    results[id][source_id] = gpg.decrypt(encrypted).data

            logger.debug("decrypted %s", results)
        else:
            results = data["data"]

        # TODO: Add filter

        # summarize
        query_id = data["query_id"]
        logger.debug("%s: %s", query_id)
        response = ""
        self.request.sendall(bytes(response, "utf-8"))

if __name__ == "__main__":
    HOST, PORT = "localhost", 50030

    server = socketserver.TCPServer((HOST, PORT), SummaryHandler)
    server.serve_forever()
