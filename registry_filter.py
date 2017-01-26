#!/usr/bin/env python3

"""
Filter parsing and filtering
"""

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

class Filter(object):

    def filter(self, query):
        for dataowner, fields in query.items():
            query_without_dataowner = query.copy()
            del query_without_dataowner[dataowner]
            for other_dataowner, other_fields in query.items():
                if dataowner == other_dataowner:
                    continue
                side_a = filters['rootlevel'][dataowner][other_dataowner]
                side_b = filters['rootlevel'][other_dataowner][dataowner]
                if side_a and side_b:
                    continue
                else:
                    return False
        return True


if __name__ == '__main__':
    query = {
        'hunt': ['age', 'gender'],
        'cancer': ['lung_cancer'],
        }
    f = Filter('hunt')
    status = f.filter(query)
    print(status, "ST")
