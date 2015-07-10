#!/usr/bin/env python3

"""
This will simulate sending email results.
"""

import os
import gnupg
import logging
import socketserver
from lib import get_config, decrypt

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
logging.getLogger("gnupg").setLevel(logging.INFO)
logger = logging.getLogger('summary')

config = get_config()

encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


class PresentationHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        data = decrypt(self.data)

        decrypted_data = {
            decrypt(encrypted_key): summary
            for encrypted_key, summary in data.items()
        }

        logger.info("decrypted summary: %s", decrypted_data)

        response = ""
        self.request.sendall(bytes(response, "utf-8"))

if __name__ == "__main__":
    HOST, PORT = "localhost", 50040

    server = socketserver.TCPServer((HOST, PORT), PresentationHandler)
    server.serve_forever()
