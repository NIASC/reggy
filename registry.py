#!/usr/bin/env python3

"""
This will mimic a health registry, not using correct data, but something
similar.
"""

import os
import json
import csv
import base64
import gnupg
import socket
import logging
import scrypt

from lib import get_config, encrypt, decrypt, send_data

from flask import Flask, render_template, redirect

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('registry')

config = get_config()
# get encryption config from config file
# keydir could be null in the file to use the default key folder
encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

hash_config = config.get('hashing', {})

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


def find_indexes_from_fieldnames(headers, fieldnames):
    indexes = []
    for fieldname in fieldnames:
        try:
            index = headers.index(fieldname)
            indexes.append(index)
        except ValueError:
            pass
    return indexes


def hash_id(original_id, salt):
    hashed_id = scrypt.hash(original_id, salt)
    logger.debug("hashed %s to %s using salt %s", original_id, hashed_id, salt)
    encoded_id = base64.b64encode(hashed_id)
    logger.debug("hashed_id encoded to", encoded_id)
    return encoded_id.decode("utf-8")


def get_local_data(fieldnames, source_id):
    """
    Read and encrypt local data. Returned in a dictionary using anonymized ids
    as keys"""
    with open(source_id + '.csv', 'r') as f:
        reader = csv.reader(f)
        tabular_data = [row for row in reader]
        headers = [h.strip() for h in tabular_data[0]]
        indexes_to_use = find_indexes_from_fieldnames(headers, fieldnames)
        data = {}
        for line in tabular_data[1:]:
            hashed_id = hash_id(line[0], "RANDOM SALT")
            obj = {}
            for field in indexes_to_use:
                obj[headers[field]] = line[field]
            if encryption_config.get('encrypt_data', True):
                recipient_email = encryption_config.get('recipient',
                                                        'sigurdga@edge')
                obj = gpg.encrypt(json.dumps(obj), [recipient_email]).data
                obj = obj.decode("utf-8")

            data[hashed_id] = obj
        return {'data': data, 'source_id': source_id}


def fetch_queries(source_id):
    logger.debug("fetching queries")
    HOST, PORT = "localhost", 50010
    data = json.dumps({"source_id": source_id})

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    received = None
    all_signed_queries = []
    this_signed_queries = {}

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        logger.debug("sending       %s", data)
        sock.sendall(bytes(data, "utf-8") + bytes("\n", "utf-8"))

        # Receive data from the server and shut down
        received = sock.makefile().readline()
        logger.debug("received      %s", received)
        decrypted_data = decrypt(received)

        logger.debug("decrypted_data %s", decrypted_data)
        queries = decrypted_data['queries']
        logger.debug("queries       %s", queries)
        for query in queries:
            logger.debug("query     %s", query)
            if source_id in query['signed_by']:
                if set(query["signed_by"]) == set(query["sources"]):
                    logger.info("Is ready: %s", query["id"])
                    all_signed_queries.append(query)
                else:
                    logger.info("I have signed this, but not everybody else: %s", query["id"])

            else:
                original = query['signed']

                # verify
                verified = gpg.verify(original)
                if not verified:
                    raise ValueError(
                        "Signature could not be verified for query %s",
                        query)

                # sign
                signed = gpg.sign(original)
                this_signed_queries[query['id']] = signed.data.decode("utf-8")
        logger.debug("signed queries %s", this_signed_queries)
        encrypted = encrypt(this_signed_queries, "sigurdga@edge")
        sock.sendall(encrypted + bytes("\n", "utf-8"))

    finally:
        sock.close()

    return all_signed_queries


@app.route("/")
def index():
    return render_template('registries.html')


@app.route("/reg/<source_id>")
def queries(source_id):
    queries = fetch_queries(source_id)
    if not queries:
        raise ValueError("No queries ready yet")
    else:
        logger.debug("Queries: %s", queries)
        return render_template('queries.html',
                               queries=queries,
                               source_id=source_id)


@app.route("/<source_id>/<method>/<query_id>")
def send(source_id, method, query_id):
    queries = fetch_queries(source_id)
    if not queries:
        raise ValueError("No queries ready yet")
    else:
        logger.debug("Queries: %s", queries)
        for query in queries:
            logger.debug("Check query %s", query)
            if query["id"] == query_id:
                if method == "accept":
                    logger.info("Accepting %s", query_id)
                    fieldnames = query['fields'][source_id]
                    data = get_local_data(fieldnames, source_id)
                    data['query_id'] = query['id']
                    data['sources'] = query['sources']
                    send_data(data, "sigurdga@edge",
                              config['merge_server_port'])
                else:
                    logger.warning("Rejecting %s", query_id)
                    data = {'source_id': source_id}
                    data['query_id'] = query['id']
                    data['sources'] = query['sources']
                    send_data(data, "sigurdga@edge",
                              config['merge_server_port'])
                logger.debug("Will now redirect")
                return redirect("/reg/"+source_id)


if __name__ == '__main__':
    app.run(port=5005, debug=True)
