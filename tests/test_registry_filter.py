import unittest

from registry_filter import Filter

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

query = {
    'hunt': ['age', 'gender'],
    'cancer': ['lung_cancer'],
    }

class TestFilter(unittest.TestCase):
    def setUp(self):
        self.f = Filter()

    def test_rootlevel_both_ways(self):
        self.assertTrue(self.f.filter(query))

if __name__ == '__main__':
    unittest.main()
