#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import logging
import socketserver
from lib import get_config
from lib import decrypt_and_deserialize, decode_decrypt_and_deserialize

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('present')

config = get_config()


class PresentationHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decode_decrypt_and_deserialize(self.data)

        decrypted_data = {
            decrypt_and_deserialize(encrypted_key): summary
            for encrypted_key, summary in data.items()
        }

        logger.info("decrypted summary: %s", decrypted_data)

        response = ""
        self.request.sendall(bytes(response, "utf-8"))


if __name__ == "__main__":
    HOST, PORT = "localhost", 50040

    server = socketserver.TCPServer((HOST, PORT), PresentationHandler)
    server.serve_forever()
