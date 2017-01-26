#!/usr/bin/env python3

"""
Filter parsing and filtering.

The rootlevel filters are where we say dataowner A may be combined with dataowner B.
The leaflevel filters are where we say field A1 may be combined with field B2 (at different dataowners).

Filters are checked both ways.
"""

class Filter(object):
    def __init__(self, filters):
        self.filters = filters

    def filter(self, query):
        for dataowner, fields in query.items():
            query_without_dataowner = query.copy()
            del query_without_dataowner[dataowner]
            for other_dataowner, other_fields in query.items():
                if dataowner == other_dataowner:
                    continue
                try:
                    side_a = self.filters['rootlevel'][dataowner][other_dataowner]
                except KeyError:
                    return False
                try:
                    side_b = self.filters['rootlevel'][other_dataowner][dataowner]
                except KeyError:
                    return False
                if side_a and side_b:
                    continue
                else:
                    return False
        return True


if __name__ == '__main__':
    # Just an example. Will be removed. TODO
    query = {
        'hunt': ['age', 'gender'],
        'cancer': ['lung_cancer'],
        }
    filters = {
            'rootlevel': {
                'hunt': {
                    'cancer': True
                    },
                'cancer': {
                    'hunt': True
                    },
                },
            }

    f = Filter(filters)
    status = f.filter(query)
    print(status)
