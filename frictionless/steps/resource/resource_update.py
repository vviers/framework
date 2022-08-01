# type: ignore
from __future__ import annotations
from typing import Optional
from ...pipeline import Step
from ... import helpers


# TODO: rebase on dataclass
class resource_update(Step):
    """Update resource"""

    type = "resource-update"

    def __init__(
        self,
        *,
        name: str,
        new_name: Optional[str] = None,
        **options,
    ):
        self.name = name
        self.new_name = new_name
        self.descriptor = helpers.create_descriptor(**options)

    # State

    name: str
    """NOTE: add docs"""

    new_name: Optional[str]
    """NOTE: add docs"""

    descriptor: dict
    """NOTE: add docs"""

    # Transform

    def transform_package(self, package):
        descriptor = self.descriptor.copy()
        if self.new_name:
            descriptor["name"] = self.new_name  # type: ignore
        resource = package.get_resource(self.name)
        resource.update(descriptor)

    # Metadata

    metadata_profile_patch = {
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "newName": {"type": "string"},
        },
    }
