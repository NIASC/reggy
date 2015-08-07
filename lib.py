import os
import sys
import json
import gnupg
import base64
import socket
import logging

import config

logger = logging.getLogger(
    os.path.splitext(os.path.basename(sys.argv[0]))[0] + "-" + __name__)


def encrypt(data, recipient):
    """
    Reads recipient address from config and encrypts data for recipient
    """

    gpg = gnupg.GPG(gnupghome=config.KEYDIR)
    gpg.encoding = 'utf-8'

    logger.debug("data      %s", data)
    encrypted_data = gpg.encrypt(data, [recipient]).data
    logger.debug("encrypted %s", encrypted_data)
    return encrypted_data


def decrypt(encrypted_data):
    """
    Decrypts using GPG and parses json data structure.
    """

    gpg = gnupg.GPG(gnupghome=config.KEYDIR)
    gpg.encoding = 'utf-8'

    logger.debug("encrypted %s", encrypted_data)
    decrypted_data = gpg.decrypt(encrypted_data).data
    logger.debug("decrypted %s", decrypted_data)

    return decrypted_data


def verify(signed_data):
    """
    Decrypts using GPG and parses json data structure.
    """

    gpg = gnupg.GPG(gnupghome=config.KEYDIR)
    gpg.encoding = 'utf-8'

    return gpg.verify(signed_data)


def sign(data):
    """
    Decrypts using GPG and parses json data structure.
    """

    gpg = gnupg.GPG(gnupghome=config.KEYDIR)
    gpg.encoding = 'utf-8'

    return gpg.sign(data)


def send_data(data, encrypt_for, port, host="localhost"):
    """
    Generic way to send data using TCP
    """

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    received = None
    logger.debug("unencoded   %s", data)
    encoded_data = base64.b64encode(data)

    try:
        # Connect to server and send data
        sock.connect((host, port))
        sock.sendall(encoded_data + bytes("\n", "utf-8"))
        logger.info("sending    %s", encoded_data)

        # Receive data from the server and shut down
        received = sock.makefile().readline()

        logger.info("received   %s", received)
    finally:
        sock.close()

    return received


def decode(b64data):
    logger.debug("encoded   %s", b64data)
    return base64.b64decode(b64data)


def serialize(data):
    """
    Serialized data using json
    """

    return json.dumps(data)


def deserialize(data):
    """
    Deserialize data using json
    """

    decoded_data = None
    decoded_json_data = str(data, "utf-8")
    if (decoded_json_data):
        decoded_data = json.loads(decoded_json_data)
    return decoded_data


# Combination helpers

def serialize_and_encrypt(data, encrypt_for):
    serialized_data = serialize(data)
    encrypted_data = encrypt(serialized_data, encrypt_for)
    return encrypted_data


def serialize_encrypt_and_encode(data, encrypt_for):
    encrypted_data = serialize_and_encrypt(data, encrypt_for)
    return base64.b64encode(encrypted_data)


def serialize_encrypt_and_send(data, encrypt_for, port, host="localhost"):
    encrypted_data = serialize_and_encrypt(data, encrypt_for)
    return send_data(encrypted_data, encrypt_for, port, host="localhost")


def decrypt_and_deserialize(encrypted_data):
    decrypted_data = decrypt(encrypted_data)
    deserialized_data = deserialize(decrypted_data)
    return deserialized_data


def decode_decrypt_and_deserialize(transfered_data):
    unpacked_data = decode(transfered_data)
    deserialized_data = decrypt_and_deserialize(unpacked_data)
    return deserialized_data
