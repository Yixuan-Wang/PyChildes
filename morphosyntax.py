"""A stub for parsing morphosyntax data within CHILDES.

Namely, the Dependent Tier of Morphological Tier `%mor` and Grammatical Relations Tier `%gra`.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal, TypedDict

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

    - `feature` are irregular morphological features (with `&` tag).
    - `suffix` are regular morphemes (with `-` tag).
    - `prefix` are regular morphemes (with `#` tag).
    - `explanation` are explanations (with `=` tag).
    """
    feature: list[str]  # & tags
    suffix: list[str]  # - tags
    prefix: list[str]  # # tags
    explanation: list[str]  # = tags


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


MORPHO_LEXICAL_UNIT = {
    'marker_prefix': r'#',
    'marker_pos': r'\|',
    'marker_suffix': r'-',
    'marker_feature': r'&',
    'marker_explanation': r'=',
    'marker_subpos': r':',
    'marker_compound': r'\+',
    'marker_multiword': r'_',
    'marker_omitted': r'0+',
}

REGEX_LEXICAL_UNIT = re.compile('({})'.format('|'.join(MORPHO_LEXICAL_UNIT.values())))


def lex_morphological_component(input: str) -> list[str]:
    """Lex a morphological component into its atomic parts."""
    splits = list(filter(None, REGEX_LEXICAL_UNIT.split(input)))
    return splits


def parse_morphological_component(
    input: str, *, index: int, index_word: int, index_clitic: int
) -> MorphoComponent:
    """Parse a single morphological component, which may be a word, punctuation, or compound word."""
    lemma = ''
    buffer = ''

    pos = ''
    feature = MorphoFeature(
        feature=[],
        suffix=[],
        prefix=[],
        explanation=[],
    )
    metadata: dict[str, Any] = {
        'index_word': index_word,
        'index_clitic': index_clitic,
    }

    list_lex = lex_morphological_component(input)
    idx_lex = 0
    is_compound = False
    is_writing_lemma = False

    try:
        while idx_lex < len(list_lex):
            lex = list_lex[idx_lex]

            if lex == MORPHO_LEXICAL_UNIT['marker_prefix']:
                feature['prefix'].append(list_lex[idx_lex - 1])
                idx_lex += 1
            elif lex == '|':
                pos = buffer
                is_writing_lemma = True
                idx_lex += 1
            elif lex == MORPHO_LEXICAL_UNIT['marker_subpos']:
                metadata['subpos'] = list_lex[idx_lex + 1]
                idx_lex += 2
            elif lex == MORPHO_LEXICAL_UNIT['marker_suffix']:
                feature['suffix'].append(list_lex[idx_lex + 1])
                idx_lex += 2
            elif lex == MORPHO_LEXICAL_UNIT['marker_feature']:
                feature['feature'].append(list_lex[idx_lex + 1])
                idx_lex += 2
            elif lex == MORPHO_LEXICAL_UNIT['marker_explanation']:
                feature['explanation'].append(list_lex[idx_lex + 1])
                idx_lex += 2
            elif lex == MORPHO_LEXICAL_UNIT['marker_multiword']:
                lemma += ' '
                idx_lex += 1
            elif lex == '+':
                if idx_lex == 0:
                    # This is a leading + punctuation
                    break

                # pos|compound+pos|compound
                is_compound = True
                is_writing_lemma = True
                compound = []
                while idx_lex < len(list_lex) and list_lex[idx_lex] == '+':
                    assert list_lex[idx_lex + 2] == '|', 'Unhandled compound morphological component'
                    compound_pos, compound_lemma = list_lex[idx_lex + 1], list_lex[idx_lex + 3]
                    compound.append({
                        'pos': compound_pos,
                        'lemma': compound_lemma,
                    })
                    lemma += compound_lemma

                    idx_lex += 4
                metadata['components'] = compound
                is_writing_lemma = False
            elif lex.startswith('0'):
                # This is a hypothetical addition of an omitted morpheme.
                # Level can be 1 or 2 zeros.
                metadata['omitted'] = len(lex)
                idx_lex += 1
            else:
                if is_writing_lemma:
                    # Lemma can be non-contigous due to multiword `_` marker.
                    lemma += lex
                else:
                    # Buffer of pos cannot be multi-part.
                    buffer = lex

                idx_lex += 1
    except IndexError:
        raise DataIntegrityError(f'Invalid morphological component: {input}')

    if not lemma:
        kind = 'punctuation'
        pos = 'punct'
        lemma = input
    elif pos in {'cm', 'end', 'beg'}:
        kind = 'punctuation'
        metadata['comma_type'] = pos
        pos = 'punct'
        lemma = ','
    elif pos == 'zero':
        kind = 'punctuation'
        pos = 'punct'
        lemma = '<unk>'  # TODO: Do not hard code <unk>
    else:
        metadata['features'] = feature
        if is_compound:
            kind = 'compound'
        elif pos:
            kind = 'word'
        else:
            raise DataIntegrityError(f'Invalid morphological component, not of any kind: {input}')

    return MorphoComponent({
        'index': index,
        'kind': kind,
        'lemma': lemma,
        'pos': pos,
        'metadata': json.dumps(metadata),
    })


RE_SPLIT_CLITIC = re.compile(r'(?<!^)~(?!$)')


def parse_morphological(content: str) -> Morphological:
    """Parse a Morphological Tier `%mor` line.

    See [CLAN manual](https://talkbank.org/0info/manuals/CLAN.pdf) section 9.2 for details.
    Each morphological form is roughly in the format of
    ```
    pos:subpos|lemma&feature
    ```

    Examples:
    ```plaintext
    pro:sub|he~aux|be&3S part|go&PRESP~inf|to v|go prep|for det:art|a n|ride prep|with det:art|the n|child&PL .
    n|+n|milk+n|shake-PL .
    co|mhm=yes .
    v|take pro:per|it prep|off det:art|the n|fire adj|care&dn-FUL-LY coord|and v|put&ZERO pro:per|it prep|on det:art|the n|plate .
    mod|must re#v|build .
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
