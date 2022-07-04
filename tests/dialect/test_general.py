import pytest
from frictionless import Resource, Dialect, FrictionlessException


# General


def test_dialect():
    dialect = Dialect()
    assert dialect.header_rows == [1]
    assert dialect.header_join == " "
    assert dialect.header_case == True


# TODO: shall we validate dialect/schema's metadata on resource.open?
@pytest.mark.skip
def test_dialect_bad_property():
    dialect = Dialect.from_descriptor({"bad": True})
    resource = Resource("data/table.csv", dialect=dialect)
    with pytest.raises(FrictionlessException) as excinfo:
        resource.open()
    error = excinfo.value.error
    assert error.code == "control-error"
    assert error.note.count("bad")