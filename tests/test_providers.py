"""Provider-layer tests. No database or network needed: the HTTP transport is patched.
Run: python -m unittest tests.test_providers   (or pytest tests/test_providers.py)"""
import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('INGEST_DIR', tempfile.mkdtemp(prefix='pravah_ingest_'))

import requests  # noqa: E402
from providers import formats, http  # noqa: E402
from providers.adapters import (OpenMeteoAdapter, OverpassRoadsAdapter, IMDAdapter, GBAAdapter,  # noqa: E402
                                build_adapters)


class Resp:
    def __init__(self, status=200, body=b''):
        self.status_code, self.content = status, body


def jbody(o):
    return json.dumps(o).encode()


GOOD_WEATHER = {"latitude": 12.97, "longitude": 77.75,
                "current": {"time": "2026-11-06T10:00", "temperature_2m": 24.1, "relative_humidity_2m": 70,
                            "precipitation": 0.2, "weather_code": 3, "wind_speed_10m": 9.0},
                "hourly": {"time": ["2026-11-06T10:00", "2026-11-06T11:00"], "precipitation": [0.1, 0.0],
                           "temperature_2m": [24, 25], "precipitation_probability": [20, 10]}}


class HttpTests(unittest.TestCase):
    def setUp(self):
        http.clear_cache()

    def test_retries_then_succeeds(self):
        seq = [Resp(503), Resp(200, b'{}')]
        with mock.patch('requests.get', side_effect=lambda *a, **k: seq.pop(0)) as g:
            r = http.fetch('https://x.test', retries=2, sleep=lambda s: None)
        self.assertTrue(r.ok)
        self.assertEqual((r.attempts, g.call_count), (2, 2))

    def test_no_retry_on_404(self):
        with mock.patch('requests.get', return_value=Resp(404)) as g:
            r = http.fetch('https://x.test', retries=3, sleep=lambda s: None)
        self.assertFalse(r.ok)
        self.assertEqual(g.call_count, 1)

    def test_timeout_exhausts_retries(self):
        with mock.patch('requests.get', side_effect=requests.Timeout('slow')) as g:
            r = http.fetch('https://x.test', retries=2, sleep=lambda s: None)
        self.assertFalse(r.ok)
        self.assertEqual((r.attempts, g.call_count), (3, 3))
        self.assertIn('Timeout', r.error)

    def test_cache_avoids_second_request(self):
        with mock.patch('requests.get', return_value=Resp(200, b'{"a":1}')) as g:
            http.fetch('https://c.test', cache_ttl=60)
            r2 = http.fetch('https://c.test', cache_ttl=60)
        self.assertTrue(r2.from_cache)
        self.assertEqual(g.call_count, 1)


class FormatTests(unittest.TestCase):
    def test_geojson(self):
        ok = jbody({"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [77, 12]}, "properties": {}}]})
        self.assertTrue(formats.validate_geojson(ok)[1]['ok'])
        self.assertFalse(formats.validate_geojson(jbody({"type": "Nope"}))[1]['ok'])
        self.assertFalse(formats.validate_geojson(b'not json')[1]['ok'])

    def test_csv(self):
        self.assertEqual(formats.parse_csv(b'a,b\n1,2\n')[1]['records'], 1)
        self.assertFalse(formats.parse_csv(b'a,b\n')[1]['ok'])

    def test_geotiff_magic(self):
        self.assertTrue(formats.validate_geotiff(b'II*\x00' + b'\0' * 12)['ok'])
        self.assertFalse(formats.validate_geotiff(b'PNG...')['ok'])

    def test_shapefile(self):
        shp = struct.pack('>i', 9994) + b'\0' * 20 + struct.pack('>i', 50) + struct.pack('<ii', 1000, 5) + b'\0' * 64
        dbf = b'\x03\x00\x00\x00' + struct.pack('<i', 3) + b'\0' * 24
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('a.shp', shp); z.writestr('a.shx', b'x'); z.writestr('a.dbf', dbf)
        rep = formats.validate_shapefile_zip(buf.getvalue())
        self.assertTrue(rep['ok'])
        self.assertEqual(rep['records'], 3)
        self.assertTrue(rep['warnings'])  # no .prj
        self.assertFalse(formats.validate_shapefile_zip(b'junk')['ok'])


class AdapterTests(unittest.TestCase):
    def setUp(self):
        http.clear_cache()

    def test_open_meteo_success_is_forecast(self):
        with mock.patch('requests.get', return_value=Resp(200, jbody(GOOD_WEATHER))):
            r = OpenMeteoAdapter(12.97, 77.75).run()
        self.assertEqual((r.status, r.classification, r.records), ('OK', 'FORECAST', 2))
        self.assertEqual(r.observed_at, '2026-11-06T10:00')
        self.assertTrue(r.checksum)

    def test_open_meteo_rejects_implausible_values(self):
        bad = json.loads(json.dumps(GOOD_WEATHER)); bad['current']['temperature_2m'] = 999
        with mock.patch('requests.get', return_value=Resp(200, jbody(bad))):
            r = OpenMeteoAdapter(12.97, 77.75).run()
        self.assertEqual((r.status, r.classification), ('INVALID', 'UNAVAILABLE'))

    def test_open_meteo_failure_never_fabricates(self):
        with mock.patch('requests.get', side_effect=requests.ConnectionError('offline')), \
                mock.patch('providers.http.time.sleep'):
            r = OpenMeteoAdapter(12.97, 77.75).run()
        self.assertEqual((r.status, r.classification, r.payload), ('FAILED', 'UNAVAILABLE', None))

    def test_overpass_valid_and_empty(self):
        good = {"osm3s": {"timestamp_osm_base": "2026-11-06T09:00:00Z"}, "elements": [
            {"type": "way", "tags": {"highway": "primary"}, "geometry": [{"lat": 12.9, "lon": 77.7}]}]}
        ad = OverpassRoadsAdapter('12.9,77.66,13.03,77.8')
        with mock.patch('requests.post', return_value=Resp(200, jbody(good))):
            r = ad.run()
        self.assertEqual((r.status, r.records, r.observed_at), ('OK', 1, '2026-11-06T09:00:00Z'))
        self.assertTrue(Path(r.storage_path).exists())
        with mock.patch('requests.post', return_value=Resp(200, jbody({"elements": []}))):
            self.assertEqual(ad.run().status, 'INVALID')

    def test_authorised_adapters_not_configured_without_env(self):
        for k in ('IMD_URL', 'IMD_API_KEY'):
            os.environ.pop(k, None)
        with mock.patch('requests.get') as g:
            r = IMDAdapter().run()
        self.assertEqual((r.status, r.classification), ('NOT_CONFIGURED', 'UNAVAILABLE'))
        self.assertEqual(r.missing_credentials, ['IMD_URL', 'IMD_API_KEY'])
        g.assert_not_called()  # no request is made, nothing is claimed

    def test_authorised_adapter_with_config_sends_key_and_validates(self):
        env = {'GBA_URL': 'https://gis.example.test/wards.geojson'}
        gj = jbody({"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
             "properties": {}}]})
        with mock.patch.dict(os.environ, env), mock.patch('requests.get', return_value=Resp(200, gj)):
            r = GBAAdapter().run()
        self.assertEqual((r.status, r.classification, r.records), ('OK', 'OFFICIAL', 1))

    def test_registry_of_adapters_covers_required_providers(self):
        keys = set(build_adapters(12.97, 77.75, '1,2,3,4'))
        self.assertEqual(keys, {'open_meteo', 'osm_roads', 'imd', 'ksndmc', 'cwc', 'gba', 'bhuvan'})


if __name__ == '__main__':
    unittest.main()
