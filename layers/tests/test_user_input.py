"""Test user input."""
from pathlib import Path

import pytest

from layers.helpers import find_next_city, parse_input

city_file = Path("data/cities_us.txt")


def test_city_file_exists():
    """Test that the city file exists."""
    assert city_file.exists()


def test_city_file_is_file():
    """Test that the city file is a file."""
    assert city_file.is_file()


argv = ["run.py", "data/cities_us.txt", "start", "New York"]


@pytest.fixture(name="city_list", scope="module")
def fixture_city_list():
    """Return the city list."""
    return parse_input(argv)


def test_city_list_strings(city_list):
    """Test that the cities are strings."""
    assert all(isinstance(item, str) for item in city_list)


@pytest.mark.parametrize(
    "city,next_city_expected",
    [
        ("New York", "Los Angeles"),
        ("Los Angeles", "Chicago"),
        ("Chicago", "Boston"),
        ("Boston", "Austin"),
    ],
)
def test_next_city(city, next_city_expected, city_list):
    """Finds next city in city list."""
    next_city = find_next_city(city_list, city)
    assert next_city == next_city_expected


def test_next_city_not_exists(city_list):
    """Finds next city in city list."""
    next_city = find_next_city(city_list, "Not a city")
    assert next_city is None


argv_eu = ["run.py", "data/cities_europe.txt"]
city_eu_list = parse_input(argv_eu)


def test_city_list_with_colons():
    """Remove commented lines from city list."""
    city_eu_list_expected = [
        "London",
        "Paris",
        "Barcelona",
        "Madrid",
        "Bilbao",
        "Berlin",
        "Munich",
        "Frankfurt",
        "Hamburg",
        "Rome",
        "Amsterdam",
        "Stockholm",
    ]
    assert city_eu_list[:12] == city_eu_list_expected
