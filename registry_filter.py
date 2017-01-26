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
        return self.toplevel_filter(query) and self.leaflevel_filter(query)

    def toplevel_filter(self, query):
        for dataowner, fields in query.items():
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

    def leaflevel_filter(self, query):
        # Useful for testing
        if not 'leaflevel' in self.filters:
            return True

        for dataowner, fields in query.items():
            for other_dataowner, other_fields in query.items():
                if dataowner == other_dataowner:
                    continue
                side_a_has_fields = dataowner in self.filters['leaflevel']
                side_b_has_fields = dataowner in self.filters['leaflevel']
                # TODO: check one side at a time
                if not side_a_has_fields and not side_b_has_fields:
                    # no detailed checking needed
                    continue
                for field in fields:
                    if field not in self.filters['leaflevel'][dataowner]:
                        return False
                    for other_dataowner in self.filters['leaflevel'][dataowner][field]:
                        for other_field in other_fields:
                            if other_field not in self.filters['leaflevel'][dataowner][field][other_dataowner]:
                                return False
                # TODO: I don't remember if I finished the above - had to attend a meeting
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
                'cancer': true
            },
            'cancer': {
                'hunt': true
            },
        },
    }

    f = Filter(filters)
    status = f.filter(query)
    print(status)
