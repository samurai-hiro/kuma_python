import httpx


class GeoApiClient:
    REVERSE_GEOCODER_URL = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress"
    ELEVATION_URL = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"

    def __init__(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon

    async def fetch_municd(self, client: httpx.AsyncClient) -> str | None:
        params: dict[str, float] = {"lat": self.lat, "lon": self.lon,}
        r = await client.get(self.REVERSE_GEOCODER_URL, params=params)
        r.raise_for_status()
        return r.json()["results"]["muniCd"]

    async def fetch_elevation(self, client: httpx.AsyncClient) -> float | None:
        params: dict[str, str | float] = {"lat": self.lat, "lon": self.lon, "outtype": "JSON",}
        r = await client.get(self.ELEVATION_URL, params=params)
        r.raise_for_status()
        return r.json()["elevation"]