from __future__ import annotations
import re
import io
import json
import pprint
import inspect
import stringcase
from pathlib import Path
from copy import deepcopy
from collections.abc import Mapping
from importlib import import_module
from typing import TYPE_CHECKING
from typing import ClassVar, Optional, Union, List, Dict, Any, Set, Type
from .exception import FrictionlessException
from .platform import platform
from . import helpers

if TYPE_CHECKING:
    from .error import Error
    from .report import Report
    from .interfaces import IDescriptor


# NOTE: review and clean this class
# NOTE: can we generate metadata_profile from dataclasses?
# NOTE: insert __init__ params docs using instance properties data?


class Metaclass(type):
    def __init__(cls, *args, **kwarts):
        if cls.metadata_profile_patch:  # type: ignore
            cls.metadata_profile = helpers.merge_jsonschema(
                cls.metadata_profile,  # type: ignore
                cls.metadata_profile_patch,  # type: ignore
            )

    def __call__(cls, *args, **kwargs):
        obj = None
        if hasattr(cls, "__create__"):
            obj = cls.__create__(*args, **kwargs)  # type: ignore
        if obj == None:
            obj = type.__call__(cls, *args, **kwargs)
        cls.__repr__ = Metadata.__repr__  # type: ignore
        obj.metadata_initiated = True
        return obj


class Metadata(metaclass=Metaclass):
    """Metadata represenation"""

    custom: dict[str, Any] = {}
    """NOTE: add docs"""

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.custom = obj.custom.copy()
        obj.metadata_defaults = cls.metadata_defaults.copy()
        obj.metadata_assigned = cls.metadata_assigned.copy()
        obj.metadata_assigned.update(kwargs.keys())
        return obj

    def __setattr__(self, name, value):
        if not name.startswith(("_", "metadata_")):
            if self.metadata_initiated:
                if value is not None:
                    self.metadata_assigned.add(name)
                elif name in self.metadata_assigned:
                    self.metadata_assigned.remove(name)
            elif isinstance(value, (list, dict)):
                self.metadata_defaults[name] = value.copy()
            elif isinstance(value, type):
                self.metadata_defaults[name] = value.__dict__.copy()
        super().__setattr__(name, value)

    def __repr__(self) -> str:
        return pprint.pformat(self.to_descriptor(), sort_dicts=False)

    # Props

    @property
    def description_html(self) -> str:
        """Description in HTML"""
        description = getattr(self, "description", "")
        try:
            html = platform.marko.convert(description)
            html = html.replace("\n", "")
            return html
        except Exception:
            return ""

    @property
    def description_text(self) -> str:
        """Description in Text"""

        class HTMLFilter(platform.html_parser.HTMLParser):
            text = ""

            def handle_data(self, data):
                self.text += data
                self.text += " "

        parser = HTMLFilter()
        parser.feed(self.description_html)
        return parser.text.strip()

    # Defined

    def list_defined(self) -> List[str]:
        defined = list(self.metadata_assigned)
        for name, default in self.metadata_defaults.items():
            value = getattr(self, name, None)
            if isinstance(value, type):
                value = value.__dict__.copy()
            if value != default:
                defined.append(name)
        return defined

    def add_defined(self, name: str) -> None:
        self.metadata_assigned.add(name)

    def has_defined(self, name: str) -> bool:
        return name in self.list_defined()

    def get_defined(self, name: str, *, default: Any = None) -> Any:
        if self.has_defined(name):
            return getattr(self, name)
        if default is not None:
            return default

    def set_not_defined(self, name: str, value: Any, *, distinct=False) -> None:
        if not self.has_defined(name) and value is not None:
            if distinct and getattr(self, name, None) == value:
                return
            setattr(self, name, value)

    # Validate

    @classmethod
    def validate_descriptor(cls, descriptor: Union[IDescriptor, str]) -> Report:
        errors = []
        timer = helpers.Timer()
        try:
            cls.from_descriptor(descriptor)
        except FrictionlessException as exception:
            errors = exception.reasons if exception.reasons else [exception.error]
        Report = import_module("frictionless").Report
        return Report.from_validation(time=timer.time, errors=errors)

    # Convert

    @classmethod
    def from_options(cls, *args, **options):
        return cls(*args, **helpers.remove_non_values(options))

    @classmethod
    def from_descriptor(cls, descriptor, **options):
        frictionless = import_module("frictionless")
        descriptor_path = None
        if isinstance(descriptor, str):
            descriptor_path = descriptor
            basepath = options.pop("basepath", None)
            descriptor = helpers.join_basepath(descriptor, basepath)
            if "basepath" in inspect.signature(cls.__init__).parameters:
                options["basepath"] = helpers.parse_basepath(descriptor)
        descriptor = cls.metadata_retrieve(descriptor)
        Class = cls.metadata_specify(type=descriptor.get("type")) or cls
        Error = Class.metadata_Error or frictionless.errors.MetadataError
        Class.metadata_transform(descriptor)
        errors = list(Class.metadata_validate(descriptor))
        if errors:
            error = Error(note="descriptor is not valid")
            raise FrictionlessException(error, reasons=errors)
        metadata = Class.metadata_import(descriptor, **options)
        if descriptor_path:
            metadata.metadata_descriptor_path = descriptor_path
            metadata.metadata_descriptor_initial = metadata.to_descriptor()
        return metadata

    def to_descriptor(self):
        descriptor = self.metadata_export()
        frictionless = import_module("frictionless")
        Error = self.metadata_Error or frictionless.errors.MetadataError
        errors = list(self.metadata_validate(descriptor))
        if errors:
            error = Error(note="descriptor is not valid")
            raise FrictionlessException(error, reasons=errors)
        return descriptor

    def to_descriptor_source(self) -> Union[IDescriptor, str]:
        """Export metadata as a descriptor or a descriptor path"""
        descriptor = self.to_descriptor()
        if self.metadata_descriptor_path:
            if self.metadata_descriptor_initial == descriptor:
                return self.metadata_descriptor_path
        return descriptor

    def to_copy(self, **options):
        """Create a copy of the metadata"""
        return type(self).from_descriptor(self.to_descriptor(), **options)

    def to_json(self, path=None, encoder_class=None):
        """Save metadata as a json

        Parameters:
            path (str): target path
        """
        frictionless = import_module("frictionless")
        Error = self.metadata_Error or frictionless.errors.MetadataError
        text = json.dumps(
            self.to_descriptor(),
            indent=2,
            ensure_ascii=False,
            cls=encoder_class,
        )
        if path:
            try:
                helpers.write_file(path, text)
            except Exception as exc:
                raise FrictionlessException(Error(note=str(exc))) from exc
        return text

    def to_yaml(self, path=None):
        """Save metadata as a yaml

        Parameters:
            path (str): target path
        """
        frictionless = import_module("frictionless")
        Error = self.metadata_Error or frictionless.errors.MetadataError
        text = platform.yaml.dump(
            self.to_descriptor(),
            sort_keys=False,
            allow_unicode=True,
            Dumper=helpers.create_yaml_dumper(),
        )
        if path:
            try:
                helpers.write_file(path, text)
            except Exception as exc:
                raise FrictionlessException(Error(note=str(exc))) from exc
        return text

    def to_markdown(self, path: Optional[str] = None, table: bool = False) -> str:
        """Convert metadata as a markdown

        This feature has been contributed to the framwork by Ethan Welty (@ezwelty):
        - https://github.com/frictionlessdata/frictionless-py/issues/837

        Parameters:
            path (str): target path
            table (bool): if true converts markdown to tabular format
        """
        frictionless = import_module("frictionless")
        Error = self.metadata_Error or frictionless.errors.MetadataError
        filename = self.__class__.__name__.lower()
        template = f"{filename}-table.md" if table is True else f"{filename}.md"
        descriptor = self.to_descriptor()
        md_output = helpers.render_markdown(f"{template}", {filename: descriptor}).strip()
        if path:
            try:
                helpers.write_file(path, md_output)
            except Exception as exc:
                raise FrictionlessException(Error(note=str(exc))) from exc
        return md_output

    # Metadata

    # TODO: add/improve types
    metadata_type: ClassVar[str]
    metadata_Error = None
    metadata_profile = {}
    metadata_profile_patch = {}
    metadata_profile_merged = {}
    metadata_initiated: bool = False
    metadata_assigned: Set[str] = set()
    metadata_defaults: Dict[str, Union[list, dict]] = {}
    metadata_descriptor_path: Optional[str] = None
    metadata_descriptor_initial: Optional[IDescriptor] = None

    @classmethod
    def metadata_retrieve(cls, descriptor: Union[IDescriptor, str]):
        try:
            if isinstance(descriptor, Mapping):
                return deepcopy(descriptor)
            if isinstance(descriptor, (str, Path)):
                if isinstance(descriptor, Path):
                    descriptor = str(descriptor)
                if helpers.is_remote_path(descriptor):
                    system = import_module("frictionless.system").system
                    http_session = system.get_http_session()
                    response = http_session.get(descriptor)
                    response.raise_for_status()
                    content = response.text
                else:
                    with open(descriptor, encoding="utf-8") as file:
                        content = file.read()
                if descriptor.endswith(".yaml"):
                    metadata = platform.yaml.safe_load(io.StringIO(content))
                else:
                    metadata = json.loads(content)
                assert isinstance(metadata, dict)
                return metadata
            raise TypeError("descriptor type is not supported")
        except Exception as exception:
            frictionless = import_module("frictionless")
            Error = cls.metadata_Error or frictionless.errors.MetadataError
            note = f'cannot retrieve metadata "{descriptor}" because "{exception}"'
            raise FrictionlessException(Error(note=note)) from exception

    @classmethod
    def metadata_specify(cls, *, type=None, property=None) -> Optional[Type[Metadata]]:
        pass

    @classmethod
    def metadata_transform(cls, descriptor: IDescriptor):
        for name in cls.metadata_profile.get("properties", {}):
            value = descriptor.get(name)
            Class = cls.metadata_specify(property=name)
            if Class:
                if isinstance(value, list):
                    for item in value:
                        if not isinstance(item, dict):
                            continue
                        ItemClass = Class.metadata_specify(type=item.get("type"))
                        if not ItemClass:
                            continue
                        ItemClass.metadata_transform(item)
                elif isinstance(value, dict):
                    Class.metadata_transform(value)

    @classmethod
    def metadata_validate(
        cls,
        descriptor: IDescriptor,
        *,
        profile: Optional[Union[IDescriptor, str]] = None,
        error_class: Optional[Type[Error]] = None,
    ):
        Error = error_class
        if not Error:
            frictionless = import_module("frictionless")
            Error = cls.metadata_Error or frictionless.errors.MetadataError
        profile = profile or cls.metadata_profile
        if isinstance(profile, str):
            profile = cls.metadata_retrieve(profile)
        validator_class = platform.jsonschema.validators.validator_for(profile)  # type: ignore
        validator = validator_class(profile)
        for error in validator.iter_errors(descriptor):
            metadata_path = "/".join(map(str, error.path))
            message = re.sub(r"\s+", " ", error.message)
            note = message
            if metadata_path:
                note = f"{note} at property '{metadata_path}'"
            yield Error(note=note)
        for name in cls.metadata_profile.get("properties", {}):
            value = descriptor.get(name)
            Class = cls.metadata_specify(property=name)
            if Class:
                if isinstance(value, list):
                    for item in value:
                        if not isinstance(item, dict):
                            continue
                        ItemClass = Class.metadata_specify(type=item.get("type"))
                        if not ItemClass:
                            continue
                        yield from ItemClass.metadata_validate(item)
                elif isinstance(value, dict):
                    yield from Class.metadata_validate(value)

    @classmethod
    def metadata_import(cls, descriptor: IDescriptor, **options):
        custom = deepcopy(descriptor)
        is_typed_class = isinstance(getattr(cls, "type", None), str)
        for name in cls.metadata_profile.get("properties", {}):
            value = custom.pop(name, None)
            if value is None or value == {}:
                continue
            if name == "type" and is_typed_class:
                continue
            Class = cls.metadata_specify(property=name)
            if Class:
                if isinstance(value, list):
                    for index, item in enumerate(value):
                        if not isinstance(item, dict):
                            continue
                        ItemClass = Class.metadata_specify(type=item.get("type"))
                        if not ItemClass:
                            continue
                        value[index] = ItemClass.metadata_import(item, **options)
                elif isinstance(value, dict):
                    value = Class.metadata_import(value)
            options.setdefault(stringcase.snakecase(name), value)
        metadata = cls(**options)
        metadata.custom = custom
        return metadata

    def metadata_export(self, *, exclude: List[str] = []) -> IDescriptor:
        descriptor = {}
        for name in self.metadata_profile.get("properties", {}):
            if name in exclude:
                continue
            if name != "type" and not self.has_defined(stringcase.snakecase(name)):
                continue
            value = getattr(self, stringcase.snakecase(name), None)
            Class = self.metadata_specify(property=name)
            if value is None or (isinstance(value, dict) and value == {}):
                continue
            if Class:
                if isinstance(value, list):
                    value = [item.to_descriptor_source() for item in value]  # type: ignore
                else:
                    value = value.to_descriptor_source()  # type: ignore
                    if not value:
                        continue
            if isinstance(value, (list, dict)):
                value = deepcopy(value)
            descriptor[name] = value
        descriptor.update(self.custom)
        return descriptor
