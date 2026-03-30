# tests/test_data_processing.py
import pytest
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


def test_generate_projected_data_skips_missing_files(tmp_path, monkeypatch):
    """Ensure generate_projected_data checks for missing input files and skips gracefully."""
    from kuskokwim_dashboard import config
    from kuskokwim_dashboard.data_processing import generate_projected_data

    # Prepare a temporary region file with one active region
    region_csv = tmp_path / "Grid_Main.csv"
    pd.DataFrame({
        "regID": ["TEST01"],
        "active": ["y"],
        "shf_scale": [1.0],
    }).to_csv(region_csv, index=False)

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "REGIONID_FILE", region_csv)

    # No SST/ICE/KU2 files are created, so this should not raise and should skip.
    generate_projected_data("20250101")

    assert not (tmp_path / "TEST01_SSTproj.csv").exists()
    assert not (tmp_path / "TEST01_BTMproj.csv").exists()
