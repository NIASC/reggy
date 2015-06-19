#!/usr/bin/env python3

"""This service will serve queries to the registrys"""

import os
import json
import gnupg
import base64
import logging
import socketserver
from urllib import request

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


def encrypt(data, recipient):
    # lots of config reading

    # get encryption config from config file
    # keydir could be null in the file to use the default key folder
    encryption_config = config.get('encryption', {})
    keydir = encryption_config.get('keydir', None)
    if not keydir:
        keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "keys")

    recipient_email = encryption_config.get('recipient', recipient)
    if not recipient_email:
        err = "Recipient %s not defined in config.json" % recipient
        logger.error(err)
        raise err

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    json_data = json.dumps(data)
    logger.debug("data        %s", json_data)
    encrypted_data = gpg.encrypt(json_data, [recipient_email]).data
    logger.debug("encrypted   %s", encrypted_data)
    encoded_data = base64.b64encode(encrypted_data)
    logger.debug("encoded     %s", encoded_data)
    return encoded_data


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
