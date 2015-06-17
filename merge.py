#!/usr/bin/env python3

"""
This will merge data when all is received

We should be able to handle queries wanting data from one provider as well as multiple.

A query will fill up ``received`` and ``query_sources``. Where ``received`` is
a list of queries we are still waiting for data for, and query_sources is a
hash of sources per query_id, for which we are waiting for data.
"""

# TODO: Do we need both, probably not, as ``received`` contains no more info
# than is provided in ``received``.

import os
import gnupg
import json
import base64
import logging
import socket
import socketserver

logger = logging.getLogger(__name__)

received = {}
query_sources = {}

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'config.json')

try:
    config = json.load(open(configfile))
except IOError:
    logger.info('Config file not found, using defaults')
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
        raise "Recipient %s not defined in config.json" % recipient

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    json_data = json.dumps(data)
    encrypted_data = gpg.encrypt(json_data, [recipient_email]).data
    encoded_data = base64.b64encode(encrypted_data)
    return encoded_data


def decrypt(data):
    encryption_config = config.get('encryption', {})
    keydir = encryption_config.get('keydir', None)
    if not keydir:
        keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "keys")

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    encrypted_data = base64.b64decode(data)
    json_data = gpg.decrypt(encrypted_data).data
    print("ost", json_data)
    decoded_json_data = str(json_data, "utf-8")
    print(decoded_json_data)
    data = json.loads(decoded_json_data)
    return data


def merge(lists):
    total = {}
    registrys = list(lists)
    print(registrys, lists)
    if registrys:
        for id in lists[registrys[0]]:
            in_all = True
            data = {}
            # doing all as this is faster than looping twice
            for registry in registrys:
                if id not in lists[registry]:
                    in_all = False
                    break
                data[registry] = lists[registry][id]
            if in_all:
                total[id] = data
    return total


def send_data(data):
    HOST, PORT = "localhost", 50030

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(data)
    received = None
    encrypted_data = encrypt(data, "sigurdga@edge")
    print(encrypted_data)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(encrypted_data + bytes("\n", "utf-8"))

        # Receive data from the server and shut down
        received = sock.makefile().readline()
        print(received)

        print("Sent:     {}".format(encrypted_data))
        print("Received: {}".format(received))
    finally:
        sock.close()

    return received


class MergeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        print("1", self.data)
        data = decrypt(self.data.decode("utf-8"))
        print("2", data)

        logger.debug("got %s", data)

        query_id = data['query_id']
        source_id = data['source_id']
        sources = data['sources']

        # first dataset using a query_id will set the acceptable sources
        if query_id not in query_sources:
            query_sources[query_id] = sources

        print(source_id, query_sources[query_id])
        if source_id not in query_sources[query_id]:
            # this is wrongly sent data. exit with bad_request
            # this should be unnecessary
            response = ""
            self.request.sendall(bytes(response, "utf-8"))

        if query_id not in received:
            received[query_id] = {}

        # if accepted by registry make data ready to merge
        if 'data' in data:
            received[query_id][source_id] = data['data']

        query_sources[query_id].remove(source_id)

        # if query_sources is emtpy, this was the last (or only) sender. data
        # should then be merged, and temporary storage should be cleaned. the
        # last step is to send the merged data to the summary server.
        if not query_sources[query_id]:
            merged = merge(received[query_id])
            logger.debug("merged %s", data)
            del received[query_id]
            del query_sources[query_id]
            data = {"query_id": query_id, "data": merged}
            send_data(data)

        logger.debug("received: %s, sources left: %s", received.keys(),
                     query_sources)

        response = ""
        self.request.sendall(bytes(response, "utf-8"))


if __name__ == '__main__':
    HOST, PORT = "localhost", 50020

    server = socketserver.TCPServer((HOST, PORT), MergeHandler)
    server.serve_forever()
