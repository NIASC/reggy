#!/usr/bin/env python2

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
import base64
import logging

from flask import Flask, render_template, redirect

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('registry')

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'config.json')

try:
    config = json.load(open(configfile))
except IOError:
    logger.info('Config file not found, using defaults')
    config = {}

# get encryption config from config file
# keydir could be null in the file to use the default key folder
encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

hash_config = config.get('hashing', {})

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


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
    b64_data = base64.b64encode(encrypted_data)
    return b64_data


def decrypt(data):
    encryption_config = config.get('encryption', {})
    keydir = encryption_config.get('keydir', None)
    if not keydir:
        keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "keys")

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    logger.debug("transferred %s", data)
    encrypted_data = base64.b64decode(data)
    logger.debug("encrypted   %s", encrypted_data)
    json_data = gpg.decrypt(encrypted_data).data
    logger.debug("decrypted   %s", json_data)
    #decoded_json_data = str(json_data, "utf-8") // not needed in python2
    data = json.loads(json_data)
    return data


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
    hash.update(hash_config.get('salt', "default salt should be overwritten"))
    hash.update(registry_person_id)
    return hash.hexdigest()


def get_local_data(fieldnames, source_id):
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
            data[id] = obj
        return {'data': data, 'source_id': source_id}


def send_data(data):

    HOST, PORT = "localhost", 50020

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(data)
    received = None

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(encrypt(data, "sigurdga@edge") + "\n")

        # Receive data from the server and shut down
        received = sock.makefile().readline()
        print(received)

        print("Sent:     {}".format(data))
        print("Received: {}".format(received))
    finally:
        sock.close()

    return received


def fetch_queries(source_id):
    logger.debug("fetching queries")
    HOST, PORT = "localhost", 50010
    data = json.dumps({"source_id": source_id})

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(data)
    received = None

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(data + "\n")

        # Receive data from the server and shut down
        received = sock.makefile().readline()
        print(received)
        decrypted_data = decrypt(received)

        print("Sent:     {}".format(data))
        print("Received: {}".format(received))
    finally:
        sock.close()

    return decrypted_data



@app.route("/")
def index():
    return render_template('registries.html')


@app.route("/<source_id>")
def queries(source_id):
    queries = fetch_queries(source_id)
    if queries:
        decoded_queries = json.loads(queries)
        return render_template('queries.html',
                               queries=decoded_queries['queries'],
                               source_id=source_id)


@app.route("/<source_id>/<method>/<query_id>")
def send(source_id, method, query_id):
    queries = fetch_queries(source_id)
    if queries:
        decoded_queries = json.loads(queries)
        for query in decoded_queries["queries"]:
            print query
            if query["id"] == query_id:
                if method == "accept":
                    fieldnames = query['fields']
                    data = get_local_data(fieldnames, source_id)
                    data['query_id'] = query['id']
                    data['sources'] = query['sources']
                    send_data(data)
                    return redirect("/"+source_id)
                else:
                    data = {'source_id': source_id}
                    data['query_id'] = query['id']
                    data['sources'] = query['sources']
                    send_data(data)
                    return redirect("/"+source_id)


if __name__ == '__main__':
    app.run(port=5005, debug=True)
