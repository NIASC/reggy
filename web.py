#!/usr/bin/env python3
# encoding: utf-8

"""
This service will serve end users, saving requests in local in-memory
database.
"""

import uuid
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, request, render_template, jsonify
# from flask import Response  # needed when returning raw data from mongo
# from bson import json_util

app = Flask(__name__)
client = MongoClient()
db = client.reggy_query


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/search", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        hunt = request.form.getlist('hunt')
        cancer = request.form.getlist('cancer')
        email = request.form.get('email')
        query = {
            "_id": uuid.uuid4().hex,
            "email": email,
            "fields": {
                "hunt": hunt,
                "cancer": cancer
            },
            "query_time": datetime.utcnow()
        }
        query_id = db.queries.insert(query)
        return (
            "Takk for din spørring. Vi sender epost når resultatene er "
            "klare.\nID {}: {}. ".format(query_id, query))
    else:
        return render_template('search.html')


@app.route("/queries")
def queries():
    queries = []
    q = db.queries.find()
    for query in q:
        # Massaging data from mongodb. This is also makes the queries jsonify-able.
        query["id"] = query.get("_id")
        query["timestamp"] = query.get("query_time").isoformat()
        del(query["_id"])
        del(query["query_time"])

        # TODO: Make the next step more generic
        # Will need a more generic solution in the web forms as well
        query["sources"] = list(query['fields'])
        queries.append(query)
    return jsonify(queries=queries)
    # Do the next if jsonify cannot be used
    #response = Response(json_util.dumps({"queries": queries}),
    #                    mimetype="application/json")
    #return response

# TODO: merge with /queries or delete completely
@app.route("/non-public/list")
def list_queries():
    queries = db.queries.find()
    return render_template('list.html', queries=queries)

# TODO: how should we delete in the future
@app.route("/non-public/empty")
def empty():
    db.queries.remove()
    return "Emptied"


if __name__ == '__main__':
    app.run(port=5000, debug=True)
