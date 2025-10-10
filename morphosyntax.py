"""A stub for parsing morphosyntax data within CHILDES.

Namely, the Dependent Tier of Morphological Tier `%mor` and Grammatical Relations Tier `%gra`.
"""

from __future__ import annotations

import json
import re
from typing import Literal, TypedDict

from utils import DataIntegrityError


class GrammaticalRelation(TypedDict):
    """A grammatical relation dictionary."""
    from_index: list[int]  # From node index
    to_index: list[int]  # To node index
    rel: list[str]  # Relation type, e.g. JCT, ROOT, PUNCT


def parse_grammatical_relations(content: str) -> GrammaticalRelation:
    """Parse a Grammatical Relations Tier `%gra` line.

    Examples:
        ```
        1|0|ROOT 2|1|JCT 3|1|JCT 4|1|PUNCT
        ```

    Returns:
        grammatical_relations(GrammaticalRelation): A list of tuples representing the parsed dependency edges,
        ready as the argument for `networkx.DiGraph.add_edges_from()`.
    """
    result = GrammaticalRelation(
        from_index=[],
        to_index=[],
        rel=[],
    )
    for entry in content.split():
        parts = entry.split('|')

        if not parts or len(parts) < 3:
            raise DataIntegrityError(f'Invalid grammatical relation entry: {entry}')

        from_index = int(parts[0])
        to_index = int(parts[1])
        rel_type = parts[2]
        result['from_index'].append(from_index)
        result['to_index'].append(to_index)
        result['rel'].append(rel_type)

    return result


class MorphoFeature(TypedDict):
    """A morphological feature dictionary.

    - `implicit` are irregular morphological features (with `&` tag).
    - `explicit` are regular morphemes (with `-` tag).
    - `explanation` are explanations (with `=` tag).
    """
    implicit: list[str]  # & tags
    explicit: list[str]  # - tags
    explanation: list[str]  # = tags


RE_SPLIT_PIPE = re.compile(r'(?<!^)\|(?!\+|$)')
RE_SPLIT_CLITIC = re.compile(r'(?<!^)~(?!$)')
RE_SPLIT_MORPH_FEATURE = re.compile(
    r'([&=-])'
)  # Must use capture group to keep the delimiters


def _parse_morphological_form(morph_form: str) -> tuple[str, MorphoFeature]:
    """Separate & and - tags from the lemma in a morphological form.

    - `&` tags indicates irregular morphological features.
    - `-` tags indicates regular morphemes (usually segmentable).
    - `=` tags indicates explanation.
    """
    feature_splits = RE_SPLIT_MORPH_FEATURE.split(morph_form)
    lemma = ''
    features: MorphoFeature = {
        'implicit': [],
        'explicit': [],
        'explanation': [],
    }

    current_delimiter: None | Literal['&', '-', '='] = None

    for part in feature_splits:
        if part in {'&', '-', '='}:
            current_delimiter = part  # type: ignore
        else:
            if current_delimiter is None:
                lemma = part
            elif current_delimiter == '&':
                features['implicit'].append(part)
            elif current_delimiter == '-':
                features['explicit'].append(part)
            elif current_delimiter == '=':
                features['explanation'].append(part)
            else:
                pass

    return lemma, features


class Morphological(TypedDict):
    """A morphological node dictionary."""
    index: list[int]
    kind: list[str]  # 'word', 'punctuation', or 'compound'
    lemma: list[str]
    pos: list[str]
    metadata: list[str]


class MorphoComponent(TypedDict):
    """A morphological component dictionary."""
    index: int
    kind: Literal['word', 'punctuation', 'compound']
    lemma: str
    pos: str
    metadata: str  # JSON string of additional metadata


def parse_morphological_component(
    component: str, *, index: int, index_word: int, index_clitic: int
) -> MorphoComponent:
    """Parse a single morphological component, which may be a word, punctuation, or compound word."""
    if component == 'cm|cm':
        return {
            'index': index,
            'kind': 'punctuation',
            'lemma': ',',
            'pos': 'punct',
            'metadata': json.dumps({
                'index_word': index_word,
                'index_clitic': index_clitic,
            })
        }

    pipe_splits = RE_SPLIT_PIPE.split(component, maxsplit=1)

    if len(pipe_splits) < 2:
        lemma = pipe_splits[0]
        return {
            'index': index,
            'kind': 'punctuation',
            'lemma': lemma,
            'pos': 'punct',
            'metadata': json.dumps({
                'index_word': index_word,
                'index_clitic': index_clitic,
            })
        }
    else:
        morph_form = pipe_splits[1]

        if morph_form.find('+') != -1:
            # This is a compound word, the pipe_split is not fully
            # e.g. n|+n|milk+n|shake-PL -> n|+n, milk+n|shake-PL
            #      n|+v|break+n|fast

            pos_total_and_1 = pipe_splits[0]

            pos_total, _, pos_1 = pos_total_and_1.partition('|+')

            morph_form_1, _, remainder = morph_form.partition('+')
            pos_2, morph_form_2 = RE_SPLIT_PIPE.split(remainder, maxsplit=1)

            lemma_1, features_1 = _parse_morphological_form(morph_form_1)
            lemma_2, features_2 = _parse_morphological_form(morph_form_2)

            return {
                'index': index,
                'kind': 'compound',
                'lemma': f'{lemma_1}{lemma_2}',
                'pos': pos_total,
                'metadata': json.dumps({
                    'index_word': index_word,
                    'index_clitic': index_clitic,
                    'components': [
                        {
                            'pos': pos_1,
                            'lemma': lemma_1,
                            'features': features_1,
                        },
                        {
                            'pos': pos_2,
                            'lemma': lemma_2,
                            'features': features_2,
                        },
                    ],
                })
            }

        lemma, features = _parse_morphological_form(morph_form)
        value = MorphoComponent({
            'index': index,
            'kind': 'word',
            'pos': pipe_splits[0],
            'lemma': lemma,
            'metadata': json.dumps({
                'index_word': index_word,
                'index_clitic': index_clitic,
                'features': features,
            }),
        })

        return value


def parse_morphological(content: str) -> Morphological:
    """Parse a Morphological Tier `%mor` line.

    See [CLAN manual](https://talkbank.org/0info/manuals/CLAN.pdf) section 9.2 for details.
    Each morphological form is roughly in the format of
    ```
    pos:subpos|lemma&feature
    ```

    Examples:
    ```
    pro:sub|he~aux|be&3S part|go&PRESP~inf|to v|go prep|for det:art|a n|ride prep|with det:art|the n|child&PL .
    n|+n|milk+n|shake-PL .
    co|mhm=yes .
    v|take pro:per|it prep|off det:art|the n|fire adj|care&dn-FUL-LY coord|and v|put&ZERO pro:per|it prep|on det:art|the n|plate .
    ```

    Returns:
        morphs(MorphoComponent): A compact representation of the morphological nodes.
    """
    morphs: Morphological = {
        'index': [],
        'kind': [],
        'lemma': [],
        'pos': [],
        'metadata': [],
    }
    index_morph = 1
    for index_word, mor_word in enumerate(content.split(' '), start=1):
        for index_clitic, mor_clitic in enumerate(
            RE_SPLIT_CLITIC.split(mor_word), start=1
        ):
            component = parse_morphological_component(
                mor_clitic,
                index=index_morph,
                index_word=index_word,
                index_clitic=index_clitic,
            )
            morphs['index'].append(component['index'])
            morphs['kind'].append(component['kind'])
            morphs['lemma'].append(component['lemma'])
            morphs['pos'].append(component['pos'])
            morphs['metadata'].append(component['metadata'])
            index_morph += 1

    return morphs
