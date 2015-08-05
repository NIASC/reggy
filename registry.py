#!/usr/bin/env python3

"""
This will mimic a health registry, not using correct data, but something
similar.
"""

import csv
import base64
import socket
import logging
import scrypt
import json
import argparse

from lib import get_config, verify, sign, serialize, serialize_and_encrypt
from lib import decode_decrypt_and_deserialize, serialize_encrypt_and_encode
from lib import serialize_encrypt_and_send


class VerificationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('registry')

config = get_config()


def find_indexes_from_fieldnames(headers, fieldnames):
    """
    Takes a list of desired field names and finds their indexes from the
    headers.
    """
    indexes = []
    for fieldname in fieldnames:
        try:
            index = headers.index(fieldname)
            indexes.append(index)
        except ValueError:
            pass
    return indexes


def generate_encrypted_fieldnames(fieldnames, source_id):
    """
    Takes list of fieldnames and generates a dict where the values are
    encrypted versions of the fieldnames. Encrypted for the presentation
    server ideally, but for the summary server for now.
    """

    return {
        fn: serialize_and_encrypt(source_id + ":" + fn,
                                  "sigurdga@edge").decode("utf-8")
        for fn in fieldnames
    }


def hash_id(original_id, salt):
    hashed_id = scrypt.hash(original_id, salt)
    logger.debug("hashed %s to %s using salt %s", original_id, hashed_id, salt)
    encoded_id = base64.b64encode(hashed_id)
    logger.debug("hashed_id encoded to %s", encoded_id)
    return encoded_id.decode("utf-8")


def get_local_data(fieldnames, source_id, salt_for_id_hashing):
    """
    Read and encrypt local data. Returned in a dictionary using anonymized
    ids as keys.

    This will be replaced with specific readers at actual registries.
    """

    with open(source_id + '.csv', 'r') as f:
        reader = csv.reader(f)
        tabular_data = [row for row in reader]
        headers = [h.strip() for h in tabular_data[0]]
        indexes_to_use = find_indexes_from_fieldnames(headers, fieldnames)
        encrypted_fieldnames = generate_encrypted_fieldnames(fieldnames,
                                                             source_id)
        data = {}
        for line in tabular_data[1:]:
            hashed_id = hash_id(line[0], salt_for_id_hashing)
            dataline = {}
            for field in indexes_to_use:
                fieldname = headers[field]
                key = encrypted_fieldnames[fieldname]
                value = line[field]
                dataline[key] = value
            dataline = serialize_and_encrypt(dataline, "sigurdga@edge")
            dataline = dataline.decode("utf-8")

            data[hashed_id] = dataline
        return {'data': data, 'source_id': source_id}


def fetch_queries(source_id):
    logger.debug("fetching queries")
    HOST, PORT = "localhost", 50010
    data = serialize({"source_id": source_id})

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
        decrypted_data = decode_decrypt_and_deserialize(received)

        logger.debug("decrypted_data %s", decrypted_data)
        if not decrypted_data:
            logger.warning("no data received")
            raise ValueError("No data received")

        queries = decrypted_data['queries']
        logger.debug("queries       %s", queries)
        for query in queries:
            logger.debug("query     %s", query)
            if source_id in query['signed_by']:
                if set(query["signed_by"]) == set(query["sources"]):
                    logger.info("Is ready: %s", query["id"])
                    all_signed_queries.append(query)
                else:
                    logger.info(
                        "I have signed this, but not everybody else: %s",
                        query["id"])

            else:
                original = query['signed']

                # verify
                verified = verify(original)
                if not verified:
                    raise VerificationError(
                        "Signature could not be verified for query %s",
                        query)

                # sign
                signed = sign(original)
                this_signed_queries[query['id']] = signed.data.decode("utf-8")
        logger.debug("signed queries %s", this_signed_queries)
        encrypted = serialize_encrypt_and_encode(this_signed_queries,
                                                 "sigurdga@edge")
        sock.sendall(encrypted + bytes("\n", "utf-8"))

    finally:
        sock.close()

    return all_signed_queries


def queries(source_id):
    try:
        queries = fetch_queries(source_id)
    except ValueError as err:
        print("No queries for {}:".format(source_id), err)
        return

    logger.debug("Queries: %s", queries)
    template = "{id!s:32}"
    print("Queries for {}\n--------------------".format(source_id))
    for query in queries:
        print(template.format(**query))
        print(json.dumps(query.get('fields'), sort_keys=True, indent=4))


def send(source_id, method, query_id):
    queries = fetch_queries(source_id)
    logger.debug("Queries: %s", queries)
    for query in queries:
        logger.debug("Check query %s", query)
        if query["id"] == query_id:
            if method == "accept":
                logger.info("Accepting %s", query_id)

                # Find field names for this source
                fieldnames = query['fields'][source_id]

                # Use signed query as salt for id hashing
                salt_for_id_hashing = query['signed']
                data = get_local_data(fieldnames,
                                      source_id,
                                      salt_for_id_hashing)

                # Copy id and total sources to data sent to merge server
                data['query_id'] = query['id']
                data['sources'] = query['sources']

                # Send data
                serialize_encrypt_and_send(data, config.MERGE_SERVER_RECIPIENT,
                                           config.MERGE_SERVER_PORT)
                return True
            else:
                logger.warning("Rejecting %s", query_id)
                data = {'source_id': source_id}
                data['query_id'] = query['id']
                data['sources'] = query['sources']
                serialize_encrypt_and_send(data, config.MERGE_SERVER_RECIPIENT,
                                           config.MERGE_SERVER_PORT)
                return True

            return


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Registry controller script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('registry', choices=("hunt", "cancer", "death"))
    parser.add_argument('--accept', type=str,
                        help="Accept one query by query ID")
    parser.add_argument('--debug', nargs="?", const=True, default=False,
                        help="Debug level for logging")
    args = parser.parse_args()

    level = logging.WARNING
    if args.debug:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    )
    logging.getLogger("gnupg").setLevel(logging.INFO)
    logger = logging.getLogger('registry')

    if not args.accept:  # or not args.reject
        # list queries for registry
        queries(args.registry)
    else:
        # accept the query
        status = send(args.registry, "accept", args.accept)
        if not status:
            logger.error("Query ID %s did not match any queries", args.accept)
