"""地域標準メッシュ（3次メッシュ）の往復・格子の検証。"""
from chiso.mesh import mesh3_code, mesh3_bbox, mesh3_center, iter_mesh3_in_bbox, BBox


def test_mesh3_roundtrip_contains_point():
    lat, lon = 36.7123, 138.4321
    code = mesh3_code(lat, lon)
    assert len(code) == 8 and code.isdigit()
    b = mesh3_bbox(code)
    assert b.min_lat <= lat < b.max_lat
    assert b.min_lon <= lon < b.max_lon


def test_mesh3_center_is_inside_and_stable():
    code = "54387300"
    clat, clon = mesh3_center(code)
    # 中心から作り直すと同じコードに戻る（決定論）
    assert mesh3_code(clat, clon) == code


def test_mesh3_cell_size_about_1km():
    b = mesh3_bbox(mesh3_code(36.7, 138.4))
    # 緯度30秒 ≒ 0.00833度, 経度45秒 = 0.0125度
    assert abs((b.max_lat - b.min_lat) - 30 / 3600) < 1e-9
    assert abs((b.max_lon - b.min_lon) - 45 / 3600) < 1e-9


def test_iter_mesh3_in_bbox_nonempty_and_sorted():
    bbox = BBox(36.60, 138.30, 36.62, 138.33)
    codes = iter_mesh3_in_bbox(bbox)
    assert codes == sorted(codes)
    assert len(codes) >= 1
    for c in codes:
        clat, clon = mesh3_center(c)
        assert bbox.contains(clat, clon)
