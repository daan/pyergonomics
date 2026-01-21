import pytest
from pathlib import Path

from pyergonomics.importers import Unit


class TestUnit:
    def test_unit_meters(self):
        assert Unit.M.value == 1.0

    def test_unit_centimeters(self):
        assert Unit.CM.value == 0.01

    def test_unit_millimeters(self):
        assert Unit.MM.value == 0.001

    def test_unit_inches(self):
        assert Unit.INCH.value == 0.0254


class TestBvhImport:
    def test_from_bvh_file_not_found(self):
        from pyergonomics.importers import from_bvh
        with pytest.raises(FileNotFoundError):
            from_bvh("nonexistent.bvh")

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath("examples/data/optitrack").exists(),
        reason="Test data not available"
    )
    def test_from_bvh_with_sample_data(self, examples_dir):
        from pyergonomics.importers import from_bvh
        bvh_files = list((examples_dir / "data" / "optitrack").glob("*.bvh"))
        if bvh_files:
            settings = from_bvh(bvh_files[0])
            assert settings is not None
            assert settings.number_of_frames > 0
