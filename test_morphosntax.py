"""Unit tests for morphosyntax parsing in prepare_childes module."""

import json
import unittest

import prepare_childes as pc

# Some example morphological components to test:
# pro:sub|he~aux|be&3S part|go&PRESP~inf|to v|go prep|for det:art|a n|ride prep|with det:art|the n|child&PL .
# n|+n|milk+n|shake-PL .
# co|mhm=yes .
# v|take pro:per|it prep|off det:art|the n|fire adj|care&dn-FUL-LY coord|and v|put&ZERO pro:per|it prep|on det:art|the n|plate .
# mod|must re#v|build .


class TestMorphosyntax(unittest.TestCase):
    """Test morphosyntax parsing functions."""
    def test_lex_morphological_component(self):
        """Test lexing of morphological components."""
        # Normal word
        self.assertEqual(
            ['n', '|', 'ride'],
            pc.morphosyntax.lex_morphological_component('n|ride')
        )

        # Punctuation
        self.assertEqual(
            ['.'],
            pc.morphosyntax.lex_morphological_component('.')
        )

        # Subpos
        self.assertEqual(
            ['pro', ':', 'sub', '|', 'he'],
            pc.morphosyntax.lex_morphological_component('pro:sub|he')
        )

        # Compound word
        self.assertEqual(
            ['n', '|', '+', 'n', '|', 'milk', '+', 'n', '|', 'shake', '-', 'PL'],
            pc.morphosyntax.lex_morphological_component('n|+n|milk+n|shake-PL')
        )

        # Complex compound
        self.assertEqual(
            ['adj', '|', 'care', '&', 'dn', '-', 'FUL', '-', 'LY'],
            pc.morphosyntax.lex_morphological_component('adj|care&dn-FUL-LY')
        )

        # Prefix marker
        self.assertEqual(
            ['re', '#', 'v', '|', 'build'],
            pc.morphosyntax.lex_morphological_component('re#v|build')
        )

    def test_parse_morphological_component(self):
        """Test parsing of morphological components."""
        # Simple word
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('n|ride', index=0, index_word=0, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 0,
                'kind': 'word',
                'lemma': 'ride',
                'pos': 'n',
                'metadata': json.dumps({
                    'index_word': 0,
                    'index_clitic': 0,
                    'features': {
                        'feature': [],
                        'suffix': [],
                        'prefix': [],
                        'explanation': [],
                    },
                }),
            })
        )

        # Punctuation
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('.', index=1, index_word=1, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 1,
                'kind': 'punctuation',
                'lemma': '.',
                'pos': 'punct',
                'metadata': json.dumps({
                    'index_word': 1,
                    'index_clitic': 0,
                }),
            })
        )

        # Word with subpos
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('pro:sub|he', index=2, index_word=2, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 2,
                'kind': 'word',
                'lemma': 'he',
                'pos': 'pro',
                'metadata': json.dumps({
                    'index_word': 2,
                    'index_clitic': 0,
                    'subpos': 'sub',
                    'features': {
                        'feature': [],
                        'suffix': [],
                        'prefix': [],
                        'explanation': [],
                    },
                }),
            })
        )

        # Word with feature
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('aux|be&3S', index=3, index_word=3, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 3,
                'kind': 'word',
                'lemma': 'be',
                'pos': 'aux',
                'metadata': json.dumps({
                    'index_word': 3,
                    'index_clitic': 0,
                    'features': {
                        'feature': ['3S'],
                        'suffix': [],
                        'prefix': [],
                        'explanation': [],
                    },
                }),
            })
        )

        # Word with suffix
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('n|child-PL', index=4, index_word=4, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 4,
                'kind': 'word',
                'lemma': 'child',
                'pos': 'n',
                'metadata': json.dumps({
                    'index_word': 4,
                    'index_clitic': 0,
                    'features': {
                        'feature': [],
                        'suffix': ['PL'],
                        'prefix': [],
                        'explanation': [],
                    },
                }),
            })
        )

        # Compound word
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('n|+n|milk+n|shake-PL', index=5, index_word=5, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 5,
                'kind': 'compound',
                'lemma': 'milkshake',
                'pos': 'n',
                'metadata': json.dumps({
                    'index_word': 5,
                    'index_clitic': 0,
                    'components': [
                        {'pos': 'n', 'lemma': 'milk'},
                        {'pos': 'n', 'lemma': 'shake'},
                    ],
                    'features': {
                        'feature': [],
                        'suffix': ['PL'],
                        'prefix': [],
                        'explanation': [],
                    },
                }),
            })
        )

        # Word with explanation
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('co|mhm=yes', index=6, index_word=6, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 6,
                'kind': 'word',
                'lemma': 'mhm',
                'pos': 'co',
                'metadata': json.dumps({
                    'index_word': 6,
                    'index_clitic': 0,
                    'features': {
                        'feature': [],
                        'suffix': [],
                        'prefix': [],
                        'explanation': ['yes'],
                    },
                }),
            })
        )

        # Word with feature and suffix
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('adj|care&dn-FUL-LY', index=7, index_word=7, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 7,
                'kind': 'word',
                'lemma': 'care',
                'pos': 'adj',
                'metadata': json.dumps({
                    'index_word': 7,
                    'index_clitic': 0,
                    'features': {
                        'feature': ['dn'],
                        'suffix': ['FUL', 'LY'],
                        'prefix': [],
                        'explanation': [],
                    },
                }),
            })
        )

        # Word with prefix
        self.assertEqual(
            pc.morphosyntax.parse_morphological_component('re#v|build', index=8, index_word=8, index_clitic=0),
            pc.morphosyntax.MorphoComponent({
                'index': 8,
                'kind': 'word',
                'lemma': 'build',
                'pos': 'v',
                'metadata': json.dumps({
                    'index_word': 8,
                    'index_clitic': 0,
                    'features': {
                        'feature': [],
                        'suffix': [],
                        'prefix': ['re'],
                        'explanation': [],
                    },
                }),
            })
        )


if __name__ == '__main__':
    unittest.main()
