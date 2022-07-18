from __future__ import annotations
import attrs
import warnings
from typing import TYPE_CHECKING, Optional, ClassVar, Iterable, List, Type
from ..metadata import Metadata
from ..system import system
from .. import settings
from .. import errors

if TYPE_CHECKING:
    from ..table import Row
    from ..error import Error
    from ..resource import Resource


# TODO: add support for validate_package/etc?
# TODO: sync API with Step (like "check.validate_resource_row")?
# TODO: API proposal: validate_package/resource=connect/resource_open/resource_row/resource_close
@attrs.define(kw_only=True)
class Check(Metadata):
    """Check representation."""

    type: ClassVar[str] = "check"
    """TODO: add docs"""

    # TODO: can it be just types not objects?
    Errors: ClassVar[List[Type[Error]]] = []
    """TODO: add docs"""

    # State

    title: Optional[str] = None
    """TODO: add docs"""

    description: Optional[str] = None
    """TODO: add docs"""

    # Props

    @property
    def resource(self) -> Resource:
        """
        Returns:
            Resource?: resource object available after the `check.connect` call
        """
        return self.__resource

    # Connect

    def connect(self, resource: Resource):
        """Connect to the given resource

        Parameters:
            resource (Resource): data resource
        """
        self.__resource = resource

    # Validate

    # TODO: fix these types Iterable -> Generator
    def validate_start(self) -> Iterable[Error]:
        """Called to validate the resource after opening

        Yields:
            Error: found errors
        """
        yield from []

    def validate_row(self, row: Row) -> Iterable[Error]:
        """Called to validate the given row (on every row)

        Parameters:
            row (Row): table row

        Yields:
            Error: found errors
        """
        yield from []

    def validate_end(self) -> Iterable[Error]:
        """Called to validate the resource before closing

        Yields:
            Error: found errors
        """
        yield from []

    # Metadata

    metadata_type = "check"
    metadata_Error = errors.CheckError
    metadata_profile = {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {"type": "string", "pattern": settings.TYPE_PATTERN},
            "title": {"type": "string"},
            "description": {"type": "string"},
        },
    }

    @classmethod
    def metadata_import(cls, descriptor):
        descriptor = cls.metadata_normalize(descriptor)

        # Type (v1.5)
        code = descriptor.pop("code", None)
        if code:
            descriptor.setdefault("type", code)
            note = 'Check "code" is deprecated in favor of "type"'
            note += "(it will be removed in the next major version)"
            warnings.warn(note, UserWarning)

        if cls is Check:
            return system.create_check(descriptor)
        return super().metadata_import(descriptor)