import pytest
from frictionless import Resource, validate


# Read


def test_stream_loader():
    with open("data/table.csv", mode="rb") as file:
        with Resource(file, format="csv") as resource:
            assert resource.header == ["id", "name"]
            assert resource.read_rows() == [
                {"id": 1, "name": "english"},
                {"id": 2, "name": "中国人"},
            ]


def test_stream_loader_text_stream():
    with open("data/table.csv") as file:
        with Resource(file, format="csv") as resource:
            assert resource.header == ["id", "name"]
            assert resource.read_rows() == [
                {"id": 1, "name": "english"},
                {"id": 2, "name": "中国人"},
            ]


def test_stream_loader_without_open():
    with open("data/table.csv", mode="rb") as file:
        resource = Resource(file, format="csv")
        assert resource.read_rows() == [
            {"id": 1, "name": "english"},
            {"id": 2, "name": "中国人"},
        ]


# Write


@pytest.mark.skip
def test_stream_loader_write():
    source = Resource("data/table.csv")
    target = source.write(scheme="stream", format="csv")
    with target:
        assert target.read_rows() == [
            {"id": 1, "name": "english"},
            {"id": 2, "name": "中国人"},
        ]


# Problems


@pytest.mark.skip
def test_stream_loader_validate_issue_740():
    with open("data/table.csv", mode="rb") as file:
        report = validate(file, format="csv")
        assert report.valid


@pytest.mark.skip
def test_stream_loader_validate_text_stream_issue_740():
    with open("data/table.csv") as file:
        report = validate(file, format="csv")
        assert report.valid