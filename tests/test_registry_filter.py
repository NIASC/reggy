import unittest

from registry_filter import Filter


class TestFilter(unittest.TestCase):
    def setUp(self):
        filters = {
            'rootlevel': {
                'hunt': {
                    'cancer': True,
                },
                'cancer': {
                    'hunt': True
                },
            },
        }
        self.f = Filter(filters)

    def test_rootlevel_both_ways(self):
        query = {
            'hunt': ['age', 'gender'],
            'cancer': ['lung_cancer'],
        }
        self.assertTrue(self.f.filter(query))

    def test_rootlevel_unknown_dataowner(self):
        query = {
            'hunt': ['age', 'gender'],
            'bad': [''],
        }
        self.assertFalse(self.f.filter(query))

if __name__ == '__main__':
    unittest.main()
