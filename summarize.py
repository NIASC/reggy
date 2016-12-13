#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import logging
import argparse
import socketserver

import config
from lib import decrypt_and_deserialize
from lib import decode_decrypt_and_deserialize, serialize_encrypt_and_send

logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('summary')


def create_summary(data):
    """
    Will just count the different values for now.

    Summary comes as a list of data. The data is again another list per
    individual of the results from the different sources. These results are
    dicts of encrypted ids and unencrypted values.
    """

    results = {}

    for individual_data in data:
        for registry_data in individual_data:
            for key, value in registry_data.items():
                if key not in results:
                    results[key] = {}
                if value not in results[key]:
                    results[key][value] = 0
                results[key][value] += 1
    return results


class SummaryHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decode_decrypt_and_deserialize(self.data)
        metadata = data["metadata"]
        query_id = data["query_id"]
        email = data["email"]

        logger.info("got data for query %s", query_id)

        results = []

        if not "data" in data:
            # rejected
            results = {"query_id": query_id, "email": email}
        else:
            # decrypt
            for dataline in data["data"]:
                line = []
                for encrypted in dataline:
                    line.append(decrypt_and_deserialize(encrypted))
                results.append(line)

            # summarize
            summary = create_summary(results)
            logger.debug("summary: %s", summary)
            results = {"data": summary, "query_id": query_id, "metadata": metadata,
                       "email": email}

        # send to next service
        serialize_encrypt_and_send(results,
                                   config.PRESENTATION_SERVER_RECIPIENT,
                                   config.PRESENTATION_SERVER_PORT)
        logger.debug("results %s decrypted: %s", query_id, results)
        response = ""
        self.request.sendall(bytes(response, "utf-8"))
        logger.info("summary for %s passed on to presentation server",
                    query_id)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Summary server")
    parser.add_argument('--debug', nargs='?', const=True, default=False,
                        help="Debug logging")
    args = parser.parse_args()

    level = logging.INFO
    if args.debug:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    )
    server = socketserver.TCPServer((config.SUMMARY_SERVER_HOST,
                                     config.SUMMARY_SERVER_PORT),
                                    SummaryHandler)
    server.serve_forever()
