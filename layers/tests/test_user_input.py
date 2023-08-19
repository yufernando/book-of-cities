from pathlib import Path

from layers.helpers import parse_user_input

city_file = Path("data/cities_us.txt")


def test_city_file_exists():
    """Test that the city file exists."""
    assert city_file.exists()


def test_city_file_is_file():
    """Test that the city file is a file."""
    assert city_file.is_file()


argv = ["run.py", "data/cities_us.txt", "start", "New York"]
city_list, cities_list, city_file_provided = parse_user_input(argv)


def test_cities_are_strings():
    """Test that the cities are strings."""
    assert all(isinstance(item, str) for item in city_list)


def test_city_file_provided():
    """Test that the city file is provided."""
    assert city_file_provided
