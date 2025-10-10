"""Module for `UnitTurn`, which represents a unit of utterance with its surrounding environmental context."""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils import DataIntegrityError

if TYPE_CHECKING:
    from morphosyntax import GrammaticalRelation, Morphological


class UnitTurn:
    """Represent a unit of utterance with its surrounding environmental context.

    This class encapsulates an utterance and its related environmental information
    before, during, and after the utterance. It provides functionality to convert
    the stored data into a consolidated list format.

    Attributes:
        speaker: Identifier of the speaker associated with this unit.
        head: A list representing the headers.
        utt: A list representing the core utterance content.
        sit: A list representing the environmental situation content.
        env_bef: A list containing environmental events before the utterance.
        env_dur: A list containing environmental events during the utterance.
        env_aft: A list containing environmental events after the utterance.
    """

    speaker: str
    """\
    Identifier of the speaker associated with this unit.\
    """

    head: list[str]
    """\
    List representing the headers.\
    """

    utt: list[str]
    """\
    List representing the core utterance content.\
    """

    sit: list[str]
    """\
    List representing the situational/environmental content.\
    """

    env_bef: list[str]
    """\
    Environmental events occurring before the utterance.\
    """

    env_dur: list[str]
    """\
    Environmental events occurring during the utterance.\
    """

    env_aft: list[str]
    """\
    Environmental events occurring after the utterance.\
    """

    grammatical_relations: GrammaticalRelation
    """\
    Grammatical relations (edges in dependency grammar) associated with the utterance.\
    """

    morphological: Morphological
    """\
    Morphological components (vertices in dependency grammar) associated with the utterance.\
    """

    def __init__(self) -> None:
        """Initialize UnitUtterance with empty lists for utterance and environmental context.

        The utterance and each environmental context (before, during, after)
        are initialized as empty lists, ready to be populated with relevant data.
        """
        self.speaker = ''
        self.head = []
        self.utt = []
        self.sit = []
        self.env_bef = []
        self.env_dur = []
        self.env_aft = []

        self.grammatical_relations = {
            'from_index': [],
            'to_index': [],
            'rel': [],
        }
        self.morphological = {
            'index': [],
            'kind': [],
            'lemma': [],
            'pos': [],
            'metadata': [],
        }

    def update(self, content: str, attribute: str) -> None:
        """Append content to the specified class attribute if it exists.

        Args:
            content: The content to be appended.
            attribute: The name of the attribute to which the content will be appended.

        Raises:
            DataIntegrityError: If the specified attribute does not exist.
        """
        if hasattr(self, attribute):
            attr = getattr(self, attribute)
            if isinstance(attr, list):
                attr.append(content)
            elif isinstance(attr, str):
                setattr(self, attribute, content)
            else:
                raise DataIntegrityError(
                    f"Attribute '{attribute}' is not a list.", attribute
                )
        else:
            raise DataIntegrityError(
                f"Attribute '{attribute}' does not exist.", attribute
            )

    def to_list(self) -> list:
        """Convert the utterance and its environmental context into a single list.

        This method consolidates the environmental context (before, during, after)
        and the utterance itself into one sequential list.

        Returns:
            A list containing the combined data from env_bef, env_dur, utt, and env_aft.
        """
        output = []
        output.extend(self.head)
        output.extend(self.sit)
        output.extend(self.env_bef)
        output.extend(self.env_dur)
        output.extend(self.utt)
        output.extend(self.env_aft)
        return output

    def to_morphosyntax_graph(self) -> tuple[Morphological, GrammaticalRelation]:
        """Get the morphological components and grammatical relations.

        Returns:
            morphosyntax_graph: A tuple containing two lists:
            - The first list contains morphological components, where `index` is the node ID.
            - The second list contains grammatical relations, where `from_index` and `to_index` are node IDs.
        """
        return self.morphological, self.grammatical_relations
