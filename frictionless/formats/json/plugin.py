from ...plugin import Plugin
from .control import JsonControl
from .parser import JsonParser, JsonlParser


class JsonPlugin(Plugin):
    """Plugin for Json"""

    code = "json"

    # Hooks

    def create_control(self, descriptor):
        if descriptor.get("code") == "json":
            return JsonControl.from_descriptor(descriptor)

    def create_parser(self, resource):
        if resource.format == "json":
            return JsonParser(resource)
        elif resource.format in ["jsonl", "ndjson"]:
            return JsonlParser(resource)