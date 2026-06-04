import pytest

from src.data_loader import DEFAULT_DATASETS, load_restaurants
from src.intent import extract_intent, normalize_text
from src.models import SearchRequest
from src.search import DRINK_OR_DESSERT_ONLY_TAGS, search_restaurants


def _normalized_tags(item):
    return {normalize_text(tag) for tag in item.cuisine_tags}


def test_default_loader_merges_all_six_json_files():
    restaurants = load_restaurants()

    assert len(DEFAULT_DATASETS) == 6
    assert len(restaurants) >= 450
    assert any("han" in _normalized_tags(item) for item in restaurants)
    assert any("thai" in _normalized_tags(item) for item in restaurants)
    assert any("trung" in _normalized_tags(item) for item in restaurants)
    assert any("do tay" in _normalized_tags(item) for item in restaurants)
    assert any("che" in _normalized_tags(item) for item in restaurants)


@pytest.mark.parametrize(
    ("query", "expected_tag"),
    [
        ("quán Hàn", "hàn"),
        ("đồ Hàn", "hàn"),
        ("món Hàn Quốc", "hàn"),
        ("korean bbq", "hàn"),
        ("tokbokki", "hàn"),
        ("tteokbokki", "hàn"),
        ("quán nướng Hàn", "hàn"),
        ("BBQ Hàn Quốc", "hàn"),
        ("quán Thái", "thái"),
        ("đồ Thái", "thái"),
        ("món Thái", "thái"),
        ("pad thai", "thái"),
        ("tomyum", "thái"),
        ("tom yum", "thái"),
        ("lẩu thái", "thái"),
        ("quán Trung", "trung"),
        ("đồ Trung", "trung"),
        ("món Trung Quốc", "trung"),
        ("chinese restaurant", "trung"),
        ("dim sum", "trung"),
        ("mì Trung", "trung"),
        ("quán dimsum", "trung"),
        ("đồ Tây", "đồ tây"),
        ("món Tây", "đồ tây"),
        ("western food", "đồ tây"),
        ("pizza", "đồ tây"),
        ("burger", "đồ tây"),
        ("pasta", "đồ tây"),
        ("steak", "đồ tây"),
        ("chè", "chè"),
        ("chè khúc bạch", "chè"),
        ("tào phớ", "chè"),
        ("món ngọt", "chè"),
        ("dessert", "chè"),
        ("quán chè", "chè"),
        ("quán ăn", "quán ăn"),
        ("nhà hàng", "quán ăn"),
        ("restaurant", "quán ăn"),
        ("ăn uống", "quán ăn"),
        ("địa điểm ăn uống", "quán ăn"),
    ],
)
def test_phase1_cuisine_queries_hit_the_right_category(query, expected_tag):
    intent = extract_intent(f"{query} Hà Nội dưới 150k")
    result = search_restaurants(SearchRequest(cuisine=intent.cuisine, location=intent.location, budget=intent.budget))

    assert result.restaurants, query
    assert any(normalize_text(expected_tag) in _normalized_tags(item) for item in result.restaurants), query


@pytest.mark.parametrize("query", ["quán ăn", "nhà hàng", "restaurant", "ăn uống"])
def test_generic_food_queries_do_not_return_drink_or_dessert_only_places(query):
    intent = extract_intent(f"{query} Hà Nội dưới 150k")
    result = search_restaurants(SearchRequest(cuisine=intent.cuisine, location=intent.location, budget=intent.budget))
    non_food_tags = {normalize_text(tag) for tag in DRINK_OR_DESSERT_ONLY_TAGS}

    assert result.restaurants
    for item in result.restaurants[:25]:
        assert not _normalized_tags(item).issubset(non_food_tags), item.name
