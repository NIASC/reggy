#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import os
import json
import gnupg
import logging
import socketserver
from lib import get_config, decrypt, send_data

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('summary')

config = get_config()

# TODO: An extra layer could also do "project" or "select" on the returned data

# TODO: Put path to summarize server public key in config file

encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


def create_summary(data):
    """
    Will just count the different values for now.

    Summary comes as a list of data. The data is again another list per
    individual of the results from the different sources. These results are
    dicts of encrypted ids and nonencrypted values.
    """

    results = {}

    for individual_data in data:
        for registry_data in individual_data:
            print("reg", registry_data)
            registry_data = json.loads(registry_data)
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
        data = decrypt(self.data)

        results = []
        # decrypt
        for dataline in data["data"]:
            line = []
            for encrypted in dataline:
                line.append(gpg.decrypt(encrypted).data.decode("utf-8"))
            results.append(line)

        # summarize
        summary = create_summary(results)
        send_data(summary, "sigurdga@edge", config['presentation_server_port'])
        query_id = data["query_id"]
        logger.debug("results %s decrypted: %s", query_id, results)
        response = ""
        self.request.sendall(bytes(response, "utf-8"))
        logger.info("summary: %s", summary)

if __name__ == "__main__":
    HOST, PORT = "localhost", 50030

    server = socketserver.TCPServer((HOST, PORT), SummaryHandler)
    server.serve_forever()
