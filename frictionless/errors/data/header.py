from __future__ import annotations
import attrs
from typing import List
from .table import TableError


@attrs.define(kw_only=True)
class HeaderError(TableError):
    """Header error representation"""

    type = "header-error"
    title = "Header Error"
    description = "Cell Error"
    template = "Cell Error"
    tags = ["#table", "#header"]

    # State

    labels: List[str]
    """TODO: add docs"""

    row_numbers: List[int]
    """TODO: add docs"""

    # Metadata

    metadata_profile_patch = {
        "properties": {
            "labels": {},
            "rowNumbers": {},
        },
    }


class BlankHeaderError(HeaderError):
    type = "blank-header"
    title = "Blank Header"
    description = "This header is empty. A header should contain at least one value."
    template = "Header is completely blank"
