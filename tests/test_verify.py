from jobhunt.verify import CLOSED_MARKERS


def test_closed_markers_exist():
    assert any("no longer accepting" in m for m in CLOSED_MARKERS)
