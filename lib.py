import os
import sys
import json
import gnupg
import base64
import socket
import logging

logger = logging.getLogger(
    os.path.splitext(os.path.basename(sys.argv[0]))[0] + "-" + __name__)


def get_config():
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'config.json')

    try:
        config = json.load(open(configfile))
    except IOError:
        logger.warning('Config file not found, using defaults')
        config = {
            'query_server_host': 'localhost',
            'query_server_port': 50010,
            'merge_server_host': 'localhost',
            'merge_server_port': 50020,
            'summary_server_host': 'localhost',
            'summary_server_port': 50030,
            'presentation_server_host': 'localhost',
            'presentation_server_port': 50040
        }
    return config


def encrypt(data, recipient):
    """
    Converts data to json, encrypts using GPG and base64 encodes for
    transfer"""

    # lots of config reading
    # get encryption config from config file
    # keydir could be null in the file to use the default key folder
    config = get_config()
    encryption_config = config.get('encryption', {})
    keydir = encryption_config.get('keydir', None)
    if not keydir:
        keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "keys")

    recipient_email = encryption_config.get('recipient', recipient)
    if not recipient_email:
        err = "Recipient %s not defined in config.json" % recipient
        logger.error(err)
        raise err

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    json_data = json.dumps(data)
    logger.debug("data      %s", json_data)
    encrypted_data = gpg.encrypt(json_data, [recipient_email]).data
    logger.debug("encrypted %s", encrypted_data)
    encoded_data = base64.b64encode(encrypted_data)
    logger.debug("encoded   %s", encoded_data)
    return encoded_data


def decrypt(data):
    """
    Decodes transfered data using base64, decrypts using GPG and parses json
    data structure.
    """

    config = get_config()
    encryption_config = config.get('encryption', {})
    keydir = encryption_config.get('keydir', None)
    if not keydir:
        keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "keys")

    gpg = gnupg.GPG(gnupghome=keydir)
    gpg.encoding = 'utf-8'

    logger.debug("encoded   %s", data)
    encrypted_data = base64.b64decode(data)
    logger.debug("encrypted %s", encrypted_data)
    json_data = gpg.decrypt(encrypted_data).data
    logger.debug("data      %s", json_data)
    data = None
    decoded_json_data = str(json_data, "utf-8")
    if (decoded_json_data):
        data = json.loads(decoded_json_data)
    return data


def send_data(data, encrypt_for, port, host="localhost"):
    """Generic way to send data using TCP"""

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.debug(data)
    received = None
    encrypted_data = encrypt(data, encrypt_for)

    try:
        # Connect to server and send data
        sock.connect((host, port))
        sock.sendall(encrypted_data + bytes("\n", "utf-8"))
        logger.info("sending    %s", encrypted_data)

        # Receive data from the server and shut down
        received = sock.makefile().readline()

        logger.info("received   %s", received)
    finally:
        sock.close()

    return received
