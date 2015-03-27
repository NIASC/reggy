

"""
This will mimic the cancer registry, not using correct data, but something similar.
"""

import sys
import json
import urllib2
import csv

source_id = sys.argv[1]
query_id = sys.argv[2]

def get_local_data():
    with open(source_id + '.csv', 'r') as f:
        reader = csv.reader(f)
        tabular_data = [row for row in reader]
        headers = tabular_data[0]
        data = {}
        for line in tabular_data[1:]:
            id = line[0]
            obj = dict(zip(headers[1:], line[1:]))
            data[id] = obj
        return {'data': data, 'query_id': query_id, 'sources': ['cancer', 'hunt'], 'source_id': source_id}

def send_data(data):
    print "sending", data
    try:
        urllib2.urlopen('http://localhost:5000/', json.dumps(data))
    except urllib2.HTTPError, e:
        print e

data = get_local_data()
send_data(data)
