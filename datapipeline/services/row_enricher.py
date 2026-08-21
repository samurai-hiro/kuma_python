import asyncio

import httpx
import pandas as pd

from datapipeline.client.estat_api_client import EstatApiClient
from datapipeline.client.geo_api_client import GeoApiClient


class RowEnricher:
    def __init__(self, concurrency: int = 3) -> None:
        self.semaphore = asyncio.Semaphore(concurrency) # 同時実行数を制限するためのセマフォ


    async def enrich_latlon_row(self, client: httpx.AsyncClient, row: pd.Series) -> dict:
        """Get municd from lat/lon using GeoApiClient"""
        try:
            async with self.semaphore:
                geo_client = GeoApiClient(row["lat"], row["lon"])
                municd, elevation = await asyncio.gather(
                    geo_client.fetch_municd(client),
                    geo_client.fetch_elevation(client)
                )
                await asyncio.sleep(0.2) # API rate limit対策
                return {"municd": municd, "elevation": elevation}
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as e:
            print(f"エラー : {row['lat'], row['lon']} {e}")
            return {"municd": None, "elevation": None}

              
    async def enrich_municd_row(self, client: httpx.AsyncClient, row: pd.Series) -> dict:
        """Get regionName, population and area from municd using EstatApiClient"""
        try:
            async with self.semaphore:
                estat_client = EstatApiClient()
                (muni_name, prefecture), population, area = await asyncio.gather(
                    estat_client.fetch_region_name(client, row["municd"]),
                    estat_client.fetch_population(client, row["municd"], row["date"]),
                    estat_client.fetch_area(client, row["municd"], row["date"])
                )
                await asyncio.sleep(0.2)
                return {"muniname":muni_name, "prefecture":prefecture,
                         "population":population, "area":area}
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as e:
            print(f"エラー：{row['municd']} {e}")
            return {"muniname":None, "prefecture":None,
                         "population":None, "area":None}
        