#!/usr/bin/env python3

"""
This will mimic a health registry, not using correct data, but something
similar.
"""

import os
import json
import csv
import hashlib
import gnupg
import socket
import logging

from lib import get_config, decrypt, send_data

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


def hash_id(registry_person_id):
    hash = hashlib.sha256()
    salt = hash_config.get('salt', "default salt should be overwritten")
    hash.update(bytes(salt, "utf-8"))
    hash.update(bytes(registry_person_id, "utf-8"))
    hexdigest = hash.hexdigest()
    logger.debug("hashed %s to %s using salt %s", registry_person_id,
                 hexdigest, salt)
    return hexdigest


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
            if hash_config.get('hash_ids', True):
                id = hash_id(line[0])
            else:
                id = line[0]
            obj = {}
            for field in indexes_to_use:
                obj[headers[field]] = line[field]
            if encryption_config.get('encrypt_data', True):
                recipient_email = encryption_config.get('recipient',
                                                        'sigurdga@edge')
                obj = gpg.encrypt(json.dumps(obj), [recipient_email]).data
                obj = obj.decode("utf-8")

            data[id] = obj
        return {'data': data, 'source_id': source_id}


def fetch_queries(source_id):
    logger.debug("fetching queries")
    HOST, PORT = "localhost", 50010
    data = json.dumps({"source_id": source_id})

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    received = None

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        logger.debug("sending       %s", data)
        sock.sendall(bytes(data, "utf-8") + bytes("\n", "utf-8"))

        # Receive data from the server and shut down
        received = sock.makefile().readline()
        logger.debug("received      %s", received)
        decrypted_data = decrypt(received)
    finally:
        sock.close()

    return decrypted_data


@app.route("/")
def index():
    return render_template('registries.html')


@app.route("/reg/<source_id>")
def queries(source_id):
    queries = fetch_queries(source_id)
    if queries:
        return render_template('queries.html',
                               queries=queries['queries'],
                               source_id=source_id)


@app.route("/<source_id>/<method>/<query_id>")
def send(source_id, method, query_id):
    queries = fetch_queries(source_id)
    if queries:
        for query in queries["queries"]:
            logger.debug(query)
            if query["id"] == query_id:
                if method == "accept":
                    fieldnames = query['fields']
                    data = get_local_data(fieldnames, source_id)
                    data['query_id'] = query['id']
                    data['sources'] = query['sources']
                    send_data(data, "sigurdga@edge",
                              config['merge_server_port'])
                    return redirect("/reg/"+source_id)
                else:
                    data = {'source_id': source_id}
                    data['query_id'] = query['id']
                    data['sources'] = query['sources']
                    send_data(data, "sigurdga@edge",
                              config['merge_server_port'])
                    return redirect("/reg/"+source_id)


if __name__ == '__main__':
    app.run(port=5005, debug=True)
