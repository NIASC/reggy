#!/usr/bin/env python3

"""This service will serve queries to the registrys"""

import json
import socketserver
from urllib import request


class QueryHandler(socketserver.StreamRequestHandler):

    def handle(self):
        self.data = self.rfile.readline().strip()
        data = json.loads(self.data.decode("utf-8"))

        # TODO: Create good filter
        if 'source_id' in data and data['source_id'] in ['hunt', 'cancer']:
            registry_id = data['source_id']

            data = request.urlopen("http://localhost:5000/queries").read()
            queries = json.loads(data.decode("utf-8"))
            filtered = []
            for query in queries['queries']:
                if registry_id in query['sources']:
                    query['fields'] = query[registry_id]
                    filtered.append(query)

            response = json.dumps({"queries": filtered})

            print("{} wrote:".format(self.client_address[0]))
            print(response)
            self.request.sendall(bytes(response, "utf-8"))


if __name__ == "__main__":
    HOST, PORT = "localhost", 50010

    server = socketserver.TCPServer((HOST, PORT), QueryHandler)
    server.serve_forever()
