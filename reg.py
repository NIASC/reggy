#!/usr/bin/env python2

"""
This will mimic the cancer registry, not using correct data, but something similar.
"""

import sys
import json
import urllib2
import csv
import logging
import hashlib

source_id = sys.argv[1]

# TODO: Put salt in config file
salt = "this should be a secret string not commited in version control"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(source_id)

def find_indexes_from_fieldnames(headers, fieldnames):
    indexes = []
    for fieldname in fieldnames:
        try:
            index = headers.index(fieldname)
            indexes.append(index)
        except ValueError:
            pass
    return indexes

def hash_id(registry_person_id):
    hash = hashlib.sha256()
    hash.update(salt)
    hash.update(registry_person_id)
    return hash.hexdigest()

def get_local_data(fieldnames):
    with open(source_id + '.csv', 'r') as f:
        reader = csv.reader(f)
        tabular_data = [row for row in reader]
        headers = [ h.strip() for h in tabular_data[0] ]
        indexes_to_use = find_indexes_from_fieldnames(headers, fieldnames)
        data = {}
        for line in tabular_data[1:]:
            id = hash_id(line[0])
            obj = {}
            for field in indexes_to_use:
                obj[headers[field]] = line[field]
            data[id] = obj
        return {'data': data, 'source_id': source_id}

def send_data(data):
    logger.debug("sending: %s", data)
    try:
        urllib2.urlopen('http://localhost:5002/', json.dumps(data))
    except urllib2.HTTPError, e:
        logger.error(e)

def fetch_queries(source_id):
    logger.debug("fetching queries")
    try:
        res = urllib2.urlopen('http://localhost:5001/' + source_id)
        return res.read()
    except urllib2.HTTPError, e:
        logger.error(e)

queries = fetch_queries(source_id)
if queries:
    decoded_queries = json.loads(queries)
    for query in decoded_queries['queries']:
        fieldnames = query['fields']
        data = get_local_data(fieldnames)
        data['query_id'] = query['id']
        data['sources'] = query['sources']
        send_data(data)
