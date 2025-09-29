# tests/test_data_processing.py
import pytest
from shapely.geometry import Point
from kuskokwim_dashboard.data_processing import convert_to_360_transform

# Use pytest.mark.parametrize to test multiple scenarios easily
@pytest.mark.parametrize(
    "input_lon, input_lat, expected_lon, expected_lat",
    [
        (150.0, 60.0, -210.0, 60.0), # Eastern hemisphere
        (-150.0, 60.0, -150.0, 60.0),# Western hemisphere
        (0.0, 0.0, 0.0, 0.0),        # Prime meridian
    ],
)
def test_convert_to_360_transform(input_lon, input_lat, expected_lon, expected_lat):
    """
    Tests that the longitude transformation function works correctly.
    """
    # GIVEN an input point
    # WHEN the transformation is applied
    new_x, new_y = convert_to_360_transform(input_lon, input_lat)

    # THEN the output coordinates match the expected values
    assert new_x == pytest.approx(expected_lon)
    assert new_y == pytest.approx(expected_lat)
