#!/usr/bin/env python3

"""
This will mimic a health registry, not using correct data, but something
similar.
"""

import re
import csv
import base64
import socket
import logging
import scrypt
import json
import argparse

import config
from lib import verify, sign, serialize, serialize_and_encrypt
from lib import decode_decrypt_and_deserialize, serialize_encrypt_and_encode
from lib import serialize_encrypt_and_send


class VerificationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


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
        fn: serialize_and_encrypt(
            source_id + ":" + fn,
            config.PRESENTATION_SERVER_RECIPIENT
        ).decode("utf-8")
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

    # We will send metadata about categorization++ to be unpacked in
    # presentation step.
    metadata = {'intervals': config.FIELD_INTERVALS,
                'replacements': config.FIELD_REPLACEMENTS}

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

                # some fields have restrictions saying to categorize values
                if fieldname in config.FIELD_INTERVALS.keys():
                    floatvalue = float(line[field])
                    value = floatvalue // config.FIELD_INTERVALS[fieldname]
                else:
                    value = line[field]

                dataline[key] = value
            dataline = serialize_and_encrypt(dataline,
                                             config.SUMMARY_SERVER_RECIPIENT)
            dataline = dataline.decode("utf-8")

            data[hashed_id] = dataline
        return {'data': data, 'source_id': source_id}, metadata


def sign_queries(queries, source_id):
    """
    Will sign queries not already signed by this source. If debug info is
    turned on, this will also log info about already signed queries.
    """

    all_signed_queries = []
    this_signed_queries = {}
    for query in queries:
        logger.debug("query     %s", query)
        if source_id in query['signed_by']:
            if set(query["signed_by"]) == set(query["sources"]):
                logger.debug("Is ready: %s", query["id"])
                all_signed_queries.append(query)
            else:
                logger.debug(
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

    return all_signed_queries, this_signed_queries


def filter_query(query):
    """
    We will do something smart here. For now, we just look for an email address
    in the email field of the query.
    """
    email_pattern = r"[^@]+@[^@]+\.[^@]+"
    if 'email' in query and re.match(email_pattern, query['email']):
        return True
    else:
        # TODO: Should probably report the query in some way
        logger.debug("Query not passing filter %s", query)


def fetch_queries(source_id):
    logger.debug("fetching queries")
    data = serialize({"source_id": source_id})

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    received = None

    try:
        # Connect to server and send data
        sock.connect((config.QUERY_SERVER_HOST, config.QUERY_SERVER_PORT))
        logger.debug("sending       %s", data)
        logger.info("fetching queries from query server")
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
        logger.info("got %s queries from query server", len(queries))

        # sign queries
        all_signed_queries, this_signed_queries = sign_queries(queries, source_id)
        logger.debug("signed queries %s", this_signed_queries)

        # encrypt and return signed queries to query server
        encrypted = serialize_encrypt_and_encode(this_signed_queries,
                                                 config.QUERY_SERVER_RECIPIENT)
        logger.info("sending %s signed queries back to query server",
                    len(this_signed_queries))
        sock.sendall(encrypted + bytes("\n", "utf-8"))

    finally:
        sock.close()

    logger.info("returning %s queries signed by all participants",
                len(all_signed_queries))

    filtered_queries = [q for q in all_signed_queries if filter_query(q)]
    return filtered_queries


def list_queries(source_id):
    try:
        queries = fetch_queries(source_id)
    except ValueError as err:
        print("No queries for {}:".format(source_id), err)
        return

    logger.debug("Queries: %s", queries)
    template = "{id!s:32} {email}"
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
                logger.info("Accepting %s and sending it to merge server",
                            query_id)

                # Find field names for this source
                fieldnames = query['fields'][source_id]

                # Use signed query as salt for id hashing
                salt_for_id_hashing = query['signed']
                data, metadata = get_local_data(fieldnames,
                                                source_id,
                                                salt_for_id_hashing)

                # Copy id and total sources to data sent to merge server
                data['query_id'] = query['id']
                data['sources'] = query['sources']
                data['email'] = query['email']
                data['metadata'] = serialize_and_encrypt(
                    metadata, config.PRESENTATION_SERVER_RECIPIENT
                ).decode("utf-8")

                # Send data
                serialize_encrypt_and_send(data, config.MERGE_SERVER_RECIPIENT,
                                           config.MERGE_SERVER_PORT)
                logger.info("Accepted %s sent to merge server", query_id)
                return True
            else:
                # Reject
                logger.warning("Rejecting %s", query_id)
                data = {'source_id': source_id}
                data['query_id'] = query['id']
                data['sources'] = query['sources']
                data['email'] = query['email']
                serialize_encrypt_and_send(data, config.MERGE_SERVER_RECIPIENT,
                                           config.MERGE_SERVER_PORT)
                logger.info("Rejected %s sent to merge server", query_id)
                # TODO: Send email to person issuing query: Should happen from
                # other instance
                return True

            return


def accept_all(source_id):
    queries = fetch_queries(source_id)
    counter = 0
    for query in queries:
        status = send(source_id, "accept", query["id"])
        if status:
            counter += 1
    return counter


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Registry controller script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('registry', choices=("hunt", "cancer", "death"))
    parser.add_argument('--accept', type=str,
                        help="Accept one query by query ID")
    parser.add_argument('--reject', type=str,
                        help="Reject one query by query ID")
    parser.add_argument('--debug', nargs="?", const=True, default=False,
                        help="Debug logging")
    args = parser.parse_args()

    level = logging.INFO
    if args.debug:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    )
    logging.getLogger("gnupg").setLevel(logging.INFO)
    logger = logging.getLogger('registry')

    if not args.accept and not args.reject:
        # list queries for registry
        list_queries(args.registry)
    else:
        # accept query
        if args.accept == "all":
            status = accept_all(args.registry)
            if status is None:
                logger.error("Something wrong happened")
            else:
                logger.info("Auto-accepted %s queries", status)
        elif args.accept:
            status = send(args.registry, "accept", args.accept)
            if not status:
                logger.error("Could not accept ID %s (no match?)",
                        args.accept)
        # reject query
        elif args.reject:
            status = send(args.registry, "reject", args.reject)
            if not status:
                logger.error("Could not reject ID %s (no match?)",
                        args.reject)
        # TODO: More fine grained accept and reject status
