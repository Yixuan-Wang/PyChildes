"""A stub for parsing morphosyntax data within CHILDES.

Namely, the Dependent Tier of Morphological Tier `%mor` and Grammatical Relations Tier `%gra`.
"""

from __future__ import annotations

import re
from typing import Literal, TypedDict, Union, final

from utils import DataIntegrityError


class GrammaticalRelation(TypedDict):
    """A grammatical relation dictionary."""
    rel: str  # Relation type, e.g. JCT, ROOT, PUNCT


def parse_grammatical_relations(content: str) -> list[tuple[int, int, GrammaticalRelation]]:
    """Parse a Grammatical Relations Tier `%gra` line.

    Examples:
        ```
        1|0|ROOT 2|1|JCT 3|1|JCT 4|1|PUNCT
        ```

    Returns:
        grammatical_relations(list[tuple[int, int, GrammaticalRelation]]): A list of tuples representing the parsed dependency edges,
        ready as the argument for `networkx.DiGraph.add_edges_from()`.
    """
    result = []
    for entry in content.split():
        parts = entry.split('|')

        if not parts or len(parts) < 3:
            raise DataIntegrityError(f'Invalid grammatical relation entry: {entry}')

        from_idx = int(parts[0])
        to_idx = int(parts[1])
        rel_type = parts[2]
        result.append((from_idx, to_idx, {'rel': rel_type}))

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


class MorphoComponentBase(TypedDict):
    """Shared fields for all morphological components."""
    index_word: int
    index_clitic: int
    lemma: str
    pos: str


@final
class MorphoComponentWord(MorphoComponentBase):
    """A normal, single word morphological component."""
    kind: Literal['word']
    features: MorphoFeature


@final
class MorphoComponentPunctuation(MorphoComponentBase):
    """A punctuation, does not have POS tagging."""
    kind: Literal['punctuation']


@final
class MorphoComponentCompoundOne(TypedDict):
    """A component within a compound word."""
    pos: str
    lemma: str
    features: MorphoFeature


@final
class MorphoComponentCompound(MorphoComponentBase):
    """A compound word morphological component."""
    kind: Literal['compound']
    components: list[MorphoComponentCompoundOne]


MorphoComponent = Union[
    MorphoComponentWord, MorphoComponentPunctuation, MorphoComponentCompound
]


def parse_morphological_component(
    component: str, *, index_word: int, index_clitic: int
) -> MorphoComponent:
    """Parse a single morphological component, which may be a word, punctuation, or compound word."""
    if component == 'cm|cm':
        return MorphoComponentPunctuation(
            {
                'index_word': index_word,
                'index_clitic': index_clitic,
                'kind': 'punctuation',
                'lemma': ',',
                'pos': 'punct',
            }
        )

    pipe_splits = RE_SPLIT_PIPE.split(component, maxsplit=1)

    if len(pipe_splits) < 2:
        lemma = pipe_splits[0]
        return MorphoComponentPunctuation(
            {
                'index_word': index_word,
                'index_clitic': index_clitic,
                'kind': 'punctuation',
                'lemma': lemma,
                'pos': 'punct',
            }
        )
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

            return MorphoComponentCompound(
                {
                    'kind': 'compound',
                    'lemma': f'{lemma_1}{lemma_2}',
                    'pos': pos_total,
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
                }
            )

        lemma, features = _parse_morphological_form(morph_form)
        value = MorphoComponentWord(
            {
                'kind': 'word',
                'index_word': index_word,
                'index_clitic': index_clitic,
                'pos': pipe_splits[0],
                'lemma': lemma,
                'features': features,
            }
        )

        return value


def parse_morphological(content: str) -> list[tuple[int, MorphoComponent]]:
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
        morphs(list[tuple[int, MorphoComponent]]): A list of tuples representing the parsed morphological analyses,
        ready as the argument for `networkx.DiGraph.add_nodes_from()`.
    """
    list_morph = []
    index_morph = 1
    for index_word, mor_word in enumerate(content.split(' '), start=1):
        for index_clitic, mor_clitic in enumerate(
            RE_SPLIT_CLITIC.split(mor_word), start=1
        ):
            component = parse_morphological_component(
                mor_clitic, index_word=index_word, index_clitic=index_clitic
            )
            list_morph.append((index_morph, component))
            index_morph += 1

    return list_morph
