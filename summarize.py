#!/usr/bin/env python2

"""
This will simulate sending email results.
"""

import os
import gnupg
import json

from flask import Flask
from flask import request, jsonify
app = Flask(__name__)

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
try:
    config = json.load(open(configfile))
except IOError:
    app.logger.info('Config file not found, using defaults')
    config = {}

# TODO: This does not need to be a web server. It was just easy to do it the
# same way as the other hacks and mockups

# TODO: Add a layer between this and merge, do decrypt data from merge

# TODO: The new layer could also do "project" or "select" on the returned data

# TODO: Put path to summarize server public key in config file

encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'


@app.route("/", methods=['POST'])
def summarize():
    data = request.get_json(True)
    app.logger.debug("received %s", data)

    if encryption_config.get('encrypt_data', True):
        results = {}
        # decrypt
        for id, result in data["data"].items():
            results[id] = {}
            for source_id, encrypted in result.items():
                results[id][source_id] = gpg.decrypt(encrypted).data

        app.logger.debug("decrypted %s", results)
    else:
        results = data["data"]

    # filter TODO

    # summarize
    query_id = data["query_id"]
    size = len(results)
    app.logger.debug("%s: %s", query_id, size)
    return jsonify({})


if __name__ == '__main__':
    app.run(debug=True, port=5003)
