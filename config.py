KEYDIR = './keys'

QUERY_SERVER_HOST = 'localhost'
QUERY_SERVER_PORT = 50010
QUERY_SERVER_RECIPIENT = 'sigurdga@edge'

MERGE_SERVER_HOST = 'localhost'
MERGE_SERVER_PORT = 50020
MERGE_SERVER_RECIPIENT = 'sigurdga@edge'

SUMMARY_SERVER_HOST = 'localhost'
SUMMARY_SERVER_PORT = 50030
SUMMARY_SERVER_RECIPIENT = 'sigurdga@edge'

PRESENTATION_SERVER_HOST = 'localhost'
PRESENTATION_SERVER_PORT = 50040
PRESENTATION_SERVER_RECIPIENT = 'sigurdga@edge'

RECIPIENTS = {
    'hunt': 'sigurdga@edge',
    'cancer': 'sigurdga@edge',
    'death': 'sigurdga@edge'
}

# Field information should be set in registries

FIELD_INTERVALS = {
    'born': 5,
    'height': 2,
    'weight': 5
}

FIELD_REPLACEMENTS = {
    'training': {'0': 'no',
                 '1': 'one time per week',
                 '2': '2-3 times per week',
                 '3': 'a lot'},
    'smoking': {'0': 'no',
                '1': 'at parties',
                '2': 'some',
                '3': 'too much'},
    'drinking': {'0': 'never',
                 '1': 'sometimes',
                 '2': 'often',
                 '3': 'too often'}
}

# TODO: Override these when finding a file containing local config
