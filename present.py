#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import logging
import socketserver

import config
import argparse
from lib import decrypt_and_deserialize, decode_decrypt_and_deserialize

logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('present')


class PresentationHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decode_decrypt_and_deserialize(self.data)

        logging.info("got data for query %s", data["query_id"])

        # unwrap metadata organized per source
        metadata = {k: decrypt_and_deserialize(m)
                    for k, m in data["metadata"].items()}
        unwrapped_metadata = {}
        for source in metadata:
            for key in metadata[source]:
                unwrapped_metadata[source + ":" + key] = metadata[source][key]

        decrypted_data = {}
        for encrypted_fieldname, categorized_summary in data["data"].items():
            fieldname = decrypt_and_deserialize(encrypted_fieldname)
            if fieldname in unwrapped_metadata:  # replace interval categories
                summary = {int(key) * unwrapped_metadata[fieldname]: value
                           for key, value in categorized_summary.items()}
            else:
                summary = categorized_summary
            decrypted_data[fieldname] = summary

        # TODO: Logging is not the final delivery
        logger.info("decrypted summary for %s: %s",
                    data["query_id"], decrypted_data)

        response = ""
        self.request.sendall(bytes(response, "utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Result presentation server")
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
    server = socketserver.TCPServer((config.PRESENTATION_SERVER_HOST,
                                     config.PRESENTATION_SERVER_PORT),
                                    PresentationHandler)
    server.serve_forever()
