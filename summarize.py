#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import os
import gnupg
import json
import base64
import logging
import socketserver

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('summary')

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
try:
    config = json.load(open(configfile))
except IOError:
    logger.info('Config file not found, using defaults')
    config = {}

# TODO: An extra layer could also do "project" or "select" on the returned data

# TODO: Put path to summarize server public key in config file

encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


def decrypt(data):
    encryption_config = config.get('encryption', {})
    keydir = encryption_config.get('keydir', None)
    if not keydir:
        keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "keys")

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    logger.debug("encoded     %s", data)
    encrypted_data = base64.b64decode(data)
    logger.debug("encrypted   %s", encrypted_data)
    json_data = gpg.decrypt(encrypted_data).data
    logger.debug("data        %s", json_data)
    decoded_json_data = str(json_data, "utf-8")
    data = json.loads(decoded_json_data)
    return data


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
