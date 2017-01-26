import unittest
from query import filter_queries, signed_query_store


class TestQuery(unittest.TestCase):

    def test_filter_queries(self):
        signed_query_store['query_id_1'] = {'sources': ['reg1'], 'query_id': 'q1'}
        signed_query_store['query_id_2'] = {'sources': ['reg2'], 'query_id': 'q2'}
        filtered = filter_queries('reg1')
        assert filtered[0]['query_id'] == 'q1'
        assert len(filtered) == 1


if __name__ == '__main__':
    unittest.main()
