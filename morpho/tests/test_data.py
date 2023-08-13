from pathlib import Path

from morpho.layers import get_city_list

city_file = Path("data/cities_us.txt")


def test_city_file_exists():
    assert city_file.exists()


def test_city_file_is_file():
    assert city_file.is_file()


def test_cities_are_strings():
    argv = ["run.py", "data/cities_us.txt", "start", "New York"]
    city_list, *_ = get_city_list(argv)
    assert all(isinstance(item, str) for item in city_list)


def test_city_file_provided():
    argv = ["run.py", "data/cities_us.txt", "start", "New York"]
    *_, city_file_provided = get_city_list(argv)
    assert city_file_provided
