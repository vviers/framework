# type: ignore
from __future__ import annotations
from ...pipeline import Step
from ...platform import platform
from ...resource import Resource


# TODO: migrate
class table_join(Step):
    """Join tables"""

    type = "table-join"

    def __init__(
        self,
        descriptor=None,
        *,
        resource=None,
        field_name=None,
        use_hash=None,
        mode=None,
    ):
        self.setinitial("resource", resource)
        self.setinitial("fieldName", field_name)
        self.setinitial("useHash", use_hash)
        self.setinitial("mode", mode)
        super().__init__(descriptor)

    # Transform

    def transform_resource(self, resource):
        target = resource
        source = self.get("resource")
        field_name = self.get("fieldName")
        use_hash = self.get("useHash", False)
        mode = self.get("mode", "inner")
        if isinstance(source, str):
            source = target.package.get_resource(source)
        elif isinstance(source, dict):
            source = Resource(source)
        source.infer()  # type: ignore
        view1 = target.to_petl()
        view2 = source.to_petl()  # type: ignore
        if mode not in ["negate"]:
            for field in source.schema.fields:  # type: ignore
                if field.name != field_name:
                    target.schema.fields.append(field.to_copy())
        if mode == "inner":
            join = platform.petl.hashjoin if use_hash else platform.petl.join
            resource.data = join(view1, view2, field_name)  # type: ignore
        elif mode == "left":
            leftjoin = platform.petl.hashleftjoin if use_hash else platform.petl.leftjoin
            resource.data = leftjoin(view1, view2, field_name)  # type: ignore
        elif mode == "right":
            rightjoin = (
                platform.petl.hashrightjoin if use_hash else platform.petl.rightjoin
            )
            resource.data = rightjoin(view1, view2, field_name)  # type: ignore
        elif mode == "outer":
            resource.data = platform.petl.outerjoin(view1, view2, field_name)  # type: ignore
        elif mode == "cross":
            resource.data = platform.petl.crossjoin(view1, view2)  # type: ignore
        elif mode == "negate":
            antijoin = platform.petl.hashantijoin if use_hash else platform.petl.antijoin
            resource.data = antijoin(view1, view2, field_name)  # type: ignore

    # Metadata

    metadata_profile_patch = {
        "required": ["resource"],
        "properties": {
            "resource": {},
            "fieldName": {"type": "string"},
            "mode": {
                "type": "string",
                "enum": ["inner", "left", "right", "outer", "cross", "negate"],
            },
            "hash": {},
        },
    }
