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

    def test_single_field_leaflevel(self):
        filters = {
            'leaflevel': {
                'hunt': {
                    'age': {
                        'cancer': ['lung_cancer'],
                    },
                    'gender': {
                        'cancer': ['lung_cancer'],
                    },
                },
                'cancer': {
                    'lung_cancer': {
                        'hunt': ['age', 'gender'],
                    },
                },
            },
        }
        self.f = Filter(filters)
        query = {
            'hunt': ['age', 'gender'],
            'cancer': ['lung_cancer'],
        }
        self.assertTrue(self.f.leaflevel_filter(query))

    def test_missing_field_leaflevel(self):
        filters = {
            'leaflevel': {
                'hunt': {
                    'age': {
                        'cancer': ['lung_cancer'],
                    },
                },
                'cancer': {
                    'lung_cancer': {
                        'hunt': ['age'],
                    },
                },
            },
        }
        self.f = Filter(filters)
        query = {
            'hunt': ['age', 'gender'],
            'cancer': ['lung_cancer'],
        }
        self.assertFalse(self.f.leaflevel_filter(query))

    def test_missing_field_leaflevel_one_side(self):
        filters = {
            'leaflevel': {
                'hunt': {
                    'age': {
                        'cancer': ['lung_cancer'],
                    },
                },
                'cancer': {
                    'lung_cancer': {
                        'hunt': ['age', 'gender'],
                    },
                },
            },
        }
        self.f = Filter(filters)
        query = {
            'hunt': ['age', 'gender'],
            'cancer': ['lung_cancer'],
        }
        self.assertFalse(self.f.leaflevel_filter(query))

    def test_missing_field_leaflevel_other_side(self):
        filters = {
            'leaflevel': {
                'hunt': {
                    'age': {
                        'cancer': ['lung_cancer'],
                    },
                    'gender': {
                        'cancer': ['lung_cancer'],
                    },
                },
                'cancer': {
                    'lung_cancer': {
                        'hunt': ['age'],
                    },
                },
            },
        }
        self.f = Filter(filters)
        query = {
            'hunt': ['age', 'gender'],
            'cancer': ['lung_cancer'],
        }
        self.assertFalse(self.f.leaflevel_filter(query))

if __name__ == '__main__':
    unittest.main()
