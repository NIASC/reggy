#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import os
import gnupg
import logging
import socketserver
from lib import get_config, decrypt

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('summary')

config = get_config()

# TODO: An extra layer could also do "project" or "select" on the returned data

# TODO: Put path to summarize server public key in config file

encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


class SummaryHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decrypt(self.data)

        if encryption_config.get('encrypt_data', True):
            results = {}
            # decrypt
            for id, result in data["data"].items():
                results[id] = {}
                for source_id, encrypted in result.items():
                    results[id][source_id] = gpg.decrypt(encrypted).data

        else:
            results = data["data"]

        # TODO: Add filter

        # summarize
        query_id = data["query_id"]
        logger.debug("results %s decrypted: %s", query_id, results)
        response = ""
        self.request.sendall(bytes(response, "utf-8"))

if __name__ == "__main__":
    HOST, PORT = "localhost", 50030

    server = socketserver.TCPServer((HOST, PORT), SummaryHandler)
    server.serve_forever()
