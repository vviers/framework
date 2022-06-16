from typing import TYPE_CHECKING, Optional
from ..metadata import Metadata

if TYPE_CHECKING:
    from ..interfaces import IDescriptor


class Dialect2:
    delimiter: Optional[str]

    def __init__(self, *, delimiter: Optional[str] = None):
        self.delimiter = delimiter

    # Import/Export

    @staticmethod
    def from_descriptor(descriptor: IDescriptor):
        metadata = Metadata(descriptor)
        return Dialect2(
            delimiter=metadata.get("delimiter"),  # type: ignore
        )
