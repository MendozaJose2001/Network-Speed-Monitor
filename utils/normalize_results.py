# utils/normalize_results.py
"""
Speed Test Result Normalization
================================
Transforms raw speed test results from any ISpeedTest implementation
into a canonical SpeedRecord-compatible dictionary.

Design
------
All functionality is encapsulated in the SpeedTestManager class, which
is never instantiated. Normalization is driven by fuzzy header mapping
(see utils/mapp_headers.py), making it agnostic to the field naming
conventions of each ISpeedTest implementation.

Unit conversion is delegated to the record itself via get_up_down_unit()
and get_time_unit(), so SpeedTestManager never hardcodes provider-specific
scaling factors.

Conversion Rules
----------------
- Fields containing 'bps' are scaled to Mbps using the record's own
  up/down unit factor divided by 10^6.
- Fields containing 'ms' are scaled using the record's own time unit
  factor divided by 10^-3.
- Fields containing 'server' that are dicts are reduced to their 'name'
  entry only.
- All output values are cast to str to match SpeedRecord's field types.

Usage
-----
    from utils.normalize_results import SpeedTestManager

    normalized = SpeedTestManager.normalize_record(libre_speed_instance)
    record = SpeedRecord(**normalized)

Raises
------
NormalizationError
    If header mapping fails or any field cannot be converted.
"""
from models.speed_entities import SpeedRecord
from utils.mapp_headers import HeaderManager
from schemas.is_speed_test import ISpeedTest
from typing import Dict
from utils.exceptions import NormalizationError


class SpeedTestManager:
    """
    Namespace for speed test result normalization utilities.
    Never instantiate this class. All members are class-level.
    """

    # Scaling factor to convert raw bytes/s values to Mbps.
    _SCALE_UP_DOWN = 10**6

    # Scaling factor for time unit normalization to milliseconds.
    _SCALE_TIME = 10**-3

    # Number of decimal places to round normalized values to.
    _ROUNDS_DIGITS = 4

    # Reference field names derived from the canonical SpeedRecord model.
    _REFERENCE_HEADER = HeaderManager.get_header_dataclass(SpeedRecord)

    @classmethod
    def normalize_record(cls, record: ISpeedTest) -> Dict[str, str]:
        """
        Normalize a raw ISpeedTest record into a SpeedRecord-compatible dict.

        Maps input fields to canonical SpeedRecord fields using fuzzy
        matching, applies unit conversions, and casts all values to str.

        Parameters
        ----------
        record : ISpeedTest
            A raw speed test result from any ISpeedTest implementation.

        Returns
        -------
        Dict[str, str]
            A dictionary whose keys match SpeedRecord's field names and
            whose values are all strings, ready for SpeedRecord(**result).

        Raises
        ------
        NormalizationError
            If header mapping fails due to no matches above the similarity
            threshold, or if any field value cannot be converted to float
            during unit scaling.

        Example
        -------
            >>> normalized = SpeedTestManager.normalize_record(record)
            >>> SpeedRecord(**normalized)
            SpeedRecord(timestamp='...', download_mbps='95.4', ...)
        """
        try:
            record_header = HeaderManager.get_header_dataclass(record)

            mapper = HeaderManager.map_best_unique_matches(
                reference_header=cls._REFERENCE_HEADER,
                input_header=record_header
                )

        except (ValueError, TypeError) as e:
            raise NormalizationError(f"Header mapping failed: {e}")

        normalized_data = {}

        for attribute in mapper.keys():

            value = getattr(record, mapper[attribute])

            # Convert raw bytes/s to Mbps using the record's own unit factor.
            if 'bps' in attribute:
                try:
                    value = round(
                        float(value) * (record.get_up_down_unit() / cls._SCALE_UP_DOWN),
                        cls._ROUNDS_DIGITS
                        )
                except (ValueError, AttributeError) as e:
                    raise NormalizationError(
                        f"Failed to normalize field '{attribute}': {e}"
                        )

            # Normalize time values using the record's own time unit factor.
            if 'ms' in attribute:
                try:
                    value = round(
                        float(value) * (record.get_time_unit() / cls._SCALE_TIME),
                        cls._ROUNDS_DIGITS
                        )
                except (ValueError, AttributeError) as e:
                    raise NormalizationError(
                        f"Failed to normalize field '{attribute}': {e}"
                        )

            # Extract server name from dict if the field holds a server entry.
            if 'server' in attribute and isinstance(value, Dict):
                value = value.get('name')

            normalized_data[attribute] = str(value)

        return normalized_data