#!/usr/bin/env python2

"""
This will simulate sending email results
"""

from flask import Flask
from flask import request, jsonify
app = Flask(__name__)

# TODO: This does not need to be a web server. It was just easy to do it the
# same way as the other hacks and mockups

# TODO: Add a layer between this and merge, do decrypt data from merge

# TODO: The new layer could also do "project" or "select" on the returned data


@app.route("/", methods=['POST'])
def summarize():
    data = request.get_json(True)
    merged = data["data"]
    query_id = data["query_id"]
    size = len(merged)
    app.logger.debug("%s: %s", query_id, size)
    return jsonify({})


if __name__ == '__main__':
    app.run(debug=True, port=5003)
