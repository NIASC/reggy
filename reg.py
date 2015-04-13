#!/usr/bin/env python2

"""
This will mimic a health registry, not using correct data, but something similar.
"""

import os
import sys
import json
import urllib2
import csv
import logging
import hashlib
import gnupg

source_id = sys.argv[1]

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(source_id)

configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
try:
    config = json.load(open(configfile))
except IOError:
    logger.info('Config file not found, using defaults')
    config = {}

# get encryption config from config file
# keydir could be null in the file to use the default key folder
encryption_config = config.get('encryption', {})
keydir = encryption_config.get('keydir', None)
if not keydir:
    keydir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

hash_config = config.get('hashing', {})

gpg = gnupg.GPG(gnupghome=keydir)
gpg.encoding = 'utf-8'

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
    hash.update(hash_config.get('salt', "default salt should be overwritten"))
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
            if hash_config.get('hash_ids', True):
                id = hash_id(line[0])
            else:
                id = line[0]
            obj = {}
            for field in indexes_to_use:
                obj[headers[field]] = line[field]
            if encryption_config.get('encrypt_data', True):
                recipient_email = encryption_config.get('recipient', 'sigurdga@edge')
                obj = gpg.encrypt(json.dumps(obj), [recipient_email]).data
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
