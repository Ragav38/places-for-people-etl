
import pytest

from chapter_etl.transformer import transform_chapters


@pytest.fixture
def valid_feature():
    return {
        "attributes": {
            "ChapterID": "CA-0355",
            "University_Chapter": "California Polytechnic State University",
            "City": "San Luis Obispo",
            "State": "CA",
        },
        "geometry": {
            "x": -120.663191,
            "y": 35.274309,
        },
    }


def test_transform_valid_record(valid_feature):
    result = transform_chapters([valid_feature])

    assert len(result) == 1
    assert result[0]["chapter_id"] == "CA-0355"
    assert result[0]["chapter_name"] == (
        "California Polytechnic State University"
    )
    assert result[0]["city"] == "San Luis Obispo"
    assert result[0]["state"] == "CA"
    assert result[0]["longitude"] == -120.663191
    assert result[0]["latitude"] == 35.274309


def test_missing_chapter_id_raises_error(valid_feature):
    valid_feature["attributes"]["ChapterID"] = None

    with pytest.raises(ValueError, match="missing fields"):
        transform_chapters([valid_feature])


def test_non_california_record_raises_error(valid_feature):
    valid_feature["attributes"]["State"] = "NY"

    with pytest.raises(ValueError, match="Unexpected state"):
        transform_chapters([valid_feature])


def test_invalid_longitude_raises_error(valid_feature):
    valid_feature["geometry"]["x"] = -200

    with pytest.raises(ValueError, match="Invalid longitude"):
        transform_chapters([valid_feature])


def test_invalid_latitude_raises_error(valid_feature):
    valid_feature["geometry"]["y"] = 95

    with pytest.raises(ValueError, match="Invalid latitude"):
        transform_chapters([valid_feature])


def test_duplicate_chapter_id_raises_error(valid_feature):
    with pytest.raises(ValueError, match="Duplicate chapter ID"):
        transform_chapters([valid_feature, valid_feature])


def test_empty_input_returns_empty_list():
    assert transform_chapters([]) == []
