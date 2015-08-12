import unittest
from present import unwrap_metadata, insert_intervals, insert_replacements


class TestPresent(unittest.TestCase):

    def test_unwrap_metadata_simple(self):
        metadata = {'reg1': {'typ1': {'field1': True}}}
        unwrapped_metadata = unwrap_metadata(metadata)
        assert(unwrapped_metadata['typ1']['reg1:field1'])

    def test_insert_intervals(self):
        fieldname = "reg1:field1"
        metadata = {'intervals': {'reg1:field1': 5}}
        original_summary = {"5": "11", "4": "7"}
        summary = insert_intervals(fieldname, original_summary, metadata)
        keys = list(summary.keys())
        keys.sort()
        self.assertEqual(keys, [20, 25])

    def test_insert_replacements(self):
        fieldname = "reg1:field1"
        metadata = {'replacements':
                    {'reg1:field1':
                     {'cheese': 'ost', 'cake': 'kake'}
                     }
                    }
        original_summary = {'cheese': '11', 'cake': '7'}
        summary = insert_replacements(fieldname, original_summary, metadata)
        keys = list(summary.keys())
        keys.sort()
        self.assertEqual(keys, ['kake', 'ost'])


if __name__ == '__main__':
    unittest.main()
