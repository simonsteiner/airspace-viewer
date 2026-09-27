from pathlib import Path

import openair
import pytest

from app.model.openair_types import (
    AltitudeType,
    CircleGeometry,
    convert_raw_airspace,
    display_class,
)
from app.utils.airspace_colors import DEFAULT_COLOR, get_airspace_color

from .conftest import EXAMPLES, FIXTURES


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"class": "A"}, "A"),
        ({"class": "D", "type": "CTR"}, "D"),
        ({"class": "CTR"}, "CTR"),
        ({"class": "R"}, "Restricted"),
        ({"class": "Q"}, "Danger"),
        ({"class": "P"}, "Prohibited"),
        ({"class": "GP"}, "GliderProhibited"),
        ({"class": "W"}, "WaveWindow"),
        ({"class": "FFVL"}, "Ffvl"),
        ({"class": "NOTAM ref"}, "NotamRef"),
        ({"class": "UNC", "type": "R"}, "Restricted"),
        ({"class": "UNC", "type": "CTR"}, "CTR"),
        ({"class": "UNC", "type": "FIS"}, "UNC"),
        ({"class": "UNC"}, "UNC"),
        ({"class": "FOO"}, "FOO"),
    ],
)
def test_display_class(raw: dict[str, str], expected: str) -> None:
    assert display_class(raw) == expected


def test_fixture_classes_colors_and_names() -> None:
    raw = openair.parse_file(FIXTURES / "classes.txt")
    airspaces = [convert_raw_airspace(r) for r in raw]

    assert [a.airspace_class for a in airspaces] == [
        "Restricted",
        "Danger",
        "CTR",
        "Restricted",
        "FOO",
        "D",
    ]
    assert get_airspace_color("Restricted") == "#ffc107"
    assert get_airspace_color("FOO") == DEFAULT_COLOR
    # An airspace without "AN" is None in openair-rs-py >= 0.2
    assert raw[-1]["name"] is None
    assert airspaces[-1].name == ""


def test_malformed_altitude_is_other() -> None:
    raw = openair.parse_file(FIXTURES / "classes.txt")
    ctr = convert_raw_airspace(raw[2])
    assert ctr.upper_bound is not None
    assert ctr.upper_bound.type == AltitudeType.OTHER
    assert ctr.upper_bound.to_text() == "?(4500.0.5FT)"


def test_circle_centerpoint() -> None:
    raw = openair.parse_file(FIXTURES / "classes.txt")
    geom = convert_raw_airspace(raw[0]).geom
    assert isinstance(geom, CircleGeometry)
    assert geom.centerpoint == {"lat": 46.0, "lng": 8.0}


@pytest.mark.parametrize("path", sorted(EXAMPLES.iterdir()), ids=lambda p: p.name)
def test_every_example_parses(path: Path) -> None:
    raw = openair.parse_file(path)
    assert raw
    for r in raw:
        convert_raw_airspace(r)
