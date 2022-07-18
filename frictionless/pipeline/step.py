from __future__ import annotations
import attrs
import warnings
from typing import TYPE_CHECKING, ClassVar, Optional
from ..metadata import Metadata
from ..system import system
from .. import settings
from .. import errors

if TYPE_CHECKING:
    from ..package import Package
    from ..resource import Resource


# NOTE:
# We might consider migrating transform_resource API to emitting
# data as an ouput instead of setting it to target.data
# It might make custom transform steps more eloquent
# This change probably not even breaking because it will be a new
# mode supported by the system (function emiting data instead of returning None)
# We might consider adding `process_schema/row` etc to the Step class


# TODO: support something like "step.transform_resource_row"
@attrs.define(kw_only=True)
class Step(Metadata):
    """Step representation"""

    type: ClassVar[str] = "step"
    """TODO: add docs"""

    # State

    title: Optional[str] = None
    """TODO: add docs"""

    description: Optional[str] = None
    """TODO: add docs"""

    # Transform

    def transform_resource(self, resource: Resource):
        """Transform resource

        Parameters:
            resource (Resource): resource

        Returns:
            resource (Resource): resource
        """
        pass

    def transform_package(self, package: Package):
        """Transform package

        Parameters:
            package (Package): package

        Returns:
            package (Package): package
        """
        pass

    # Metadata

    metadata_type = "step"
    metadata_Error = errors.StepError
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
            note = 'Step "code" is deprecated in favor of "type"'
            note += "(it will be removed in the next major version)"
            warnings.warn(note, UserWarning)

        if cls is Step:
            return system.create_step(descriptor)  # type: ignore
        return super().metadata_import(descriptor)