import unittest
from query import filter_queries, cached_queries


class TestQuery(unittest.TestCase):

    def test_filter_queries(self):
        cached_queries['query_id_1'] = {'sources': ['reg1'], 'query_id': 'q1'}
        cached_queries['query_id_2'] = {'sources': ['reg2'], 'query_id': 'q2'}
        filtered = filter_queries('reg1')
        assert filtered['queries'][0]['query_id'] == 'q1'
        assert len(filtered) == 1


if __name__ == '__main__':
    unittest.main()
