import unittest

from merge import merge


class TestMerge(unittest.TestCase):

    def test_merge_different_ids_should_give_empty_results(self):
        data = {'reg1': {'data': {'id1': 'encrypted_data1'}},
                'reg2': {'data': {'id2': 'encrypted_data2'}}}
        merged = merge(data)

        self.assertEqual(merged, [])

    def test_merge_same_id_should_give_merged_result(self):
        data = {'reg1': {'data': {'id1': 'encrypted_data1'}},
                'reg2': {'data': {'id1': 'encrypted_data2'}}}
        merged = merge(data)

        # convert first and only line to a set for easy comparing in test
        self.assertEqual(set(merged[0]),
                         set(('encrypted_data1', 'encrypted_data2')))


if __name__ == '__main__':
    unittest.main()
