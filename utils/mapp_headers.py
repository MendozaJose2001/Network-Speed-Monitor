# utils/mapp_headers.py
"""
Header Mapping Utilities
========================
Provides fuzzy field-name matching between external data sources and
internal dataclass models. Used to reconcile naming differences between
CLI output fields and canonical model fields without requiring exact
name matches.

Design
------
All functionality is encapsulated in the HeaderManager class, which is
never instantiated. Its methods operate at the class level, keeping the
interface explicit at the call site:
HeaderManager.map_best_unique_matches(...), HeaderManager.get_header_dataclass(...).

Matching Algorithm
------------------
Uses difflib.SequenceMatcher (Ratcliff/Obershelp) to compute similarity
ratios between field name pairs. A greedy one-to-one assignment is then
applied: pairs are sorted by score descending, and each reference and
input field is consumed at most once.

The similarity threshold (_THRESHOLD_UQ_MATCH = 0.6) was selected
empirically. Adjust with care — too low risks false matches, too high
risks missing valid ones.

Future Improvements
-------------------
- Levenshtein Distance: better handling of character insertions/deletions
  if external dependencies are acceptable.
- Containment Check: boost scores for nested naming conventions
  (e.g., 'date' vs 'order_date').
- Jaro-Winkler Similarity: prioritize prefix matching, common in
  structured data schemas.

Usage
-----
    from utils.mapp_headers import HeaderManager

    reference = HeaderManager.get_header_dataclass(SpeedRecord)
    input_fields = HeaderManager.get_header_dataclass(LibreSpeedTest)
    mapping = HeaderManager.map_best_unique_matches(reference, input_fields)

Raises
------
ValueError
    If no field pairs score above the similarity threshold.
TypeError
    If the provided schema is not a dataclass.
"""
from difflib import SequenceMatcher
from dataclasses import fields, is_dataclass
from typing import List, Dict
from utils.types import DataClassProtocol


class HeaderManager:
    """
    Namespace for fuzzy header mapping utilities.
    Never instantiate this class. All members are class-level.
    """

    # Minimum similarity ratio to consider a field pair a valid match.
    # Selected empirically — adjust with care. See module docstring.
    _THRESHOLD_UQ_MATCH = 0.6

    @classmethod
    def map_best_unique_matches(
        cls,
        reference_header: List[str],
        input_header: List[str]
    ) -> Dict[str, str]:
        """
        Map input field names to reference field names by similarity score.

        Identifies the best one-to-one matches between expected field names
        (reference) and provided field names (input) using a greedy algorithm
        sorted by descending similarity ratio. Each field is matched at most
        once on both sides.

        Parameters
        ----------
        reference_header : List[str]
            Expected field names derived from the canonical data model.
        input_header : List[str]
            Actual field names received from the external data source.

        Returns
        -------
        Dict[str, str]
            A dictionary mapping each reference field name to its best
            matching input field name.

        Raises
        ------
        ValueError
            If no field pairs score at or above _THRESHOLD_UQ_MATCH.

        Notes
        -----
        Similarity is computed using difflib.SequenceMatcher, which
        implements the Ratcliff/Obershelp algorithm based on the longest
        common substrings. See module docstring for future improvement notes.

        Example
        -------
            >>> HeaderManager.map_best_unique_matches(
            ...     ['download_mbps', 'ping_ms'],
            ...     ['download', 'ping']
            ... )
            {'download_mbps': 'download', 'ping_ms': 'ping'}
        """
        score = [
            (ref, inp, SequenceMatcher(a=ref, b=inp).ratio())
            for inp in input_header
            for ref in reference_header
        ]

        score.sort(key=lambda x: x[2], reverse=True)

        mapping = {}
        used_candidates = set()

        for ref, inp, ratio in score:

            # Skip pairs that fall below the similarity threshold.
            if ratio < cls._THRESHOLD_UQ_MATCH:
                continue

            # Enforce one-to-one assignment on both sides.
            if ref not in mapping and inp not in used_candidates:
                mapping[ref] = inp
                used_candidates.add(inp)

        if not mapping:
            raise ValueError(
                f"No matches found (reference match rate {cls._THRESHOLD_UQ_MATCH})"
            )

        return mapping

    @staticmethod
    def get_header_dataclass(
        cls_schema: DataClassProtocol
    ) -> list[str]:
        """
        Extract field names from a dataclass class or instance.

        Parameters
        ----------
        cls_schema : DataClassProtocol
            A dataclass class or an instance of one from which to
            extract field names.

        Returns
        -------
        list[str]
            An ordered list of field names as defined in the dataclass.

        Raises
        ------
        TypeError
            If cls_schema is not a dataclass class or instance.

        Example
        -------
            >>> HeaderManager.get_header_dataclass(SpeedRecord)
            ['timestamp', 'download_mbps', 'upload_mbps', 'ping_ms', 'server_name']
        """
        if not is_dataclass(cls_schema):

            name = getattr(cls_schema, "__name__", str(cls_schema))

            raise TypeError(
                f"The evaluated model/schema {name} must be a dataclass schema"
            )

        return [
            field.name for field in fields(cls_schema)
        ]