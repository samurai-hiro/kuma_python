import os

import httpx
from dotenv import load_dotenv


class EstatApiClient:
    REGION_INFO_URL = "https://dashboard.e-stat.go.jp/api/1.0/Json/getRegionInfo"
    STATS_DATA_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
    STATS_DATA_ID = "0000020201" #社会・人口統計体系
    STATS_DATA_ID_2 = "0000020102" #土地面積
    CAT_CODE_POPULATION = "A1101" #人口
    CAT_CODE_AREA = "B1101" #土地面積
    load_dotenv()

    def __init__(self) -> None:
        self.api_key = os.getenv("ESTAT_API_ID")
        if not self.api_key:
            raise ValueError("ESTAT_API_ID is not set")

    async def fetch_region_name(self, client: httpx.AsyncClient, muni_cd: str) -> tuple[str | None, str | None]:
        """Fetch the name of parent region from e-stat API """
        parent_region_code = muni_cd[:2] + "000"
        params = {"ParentRegionCode": parent_region_code}
        r = await client.get(self.REGION_INFO_URL, params=params)
        r.raise_for_status()
        data = r.json()

        #県情報
        prefecture = data["GET_META_REGION_INF"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"][0]
        prefecture_name = prefecture["@name"]

        #市区情報
        regions = prefecture["CLASS"]
        muni_name = next((columns["@name"] for columns in regions if columns["@regionCode"] == muni_cd and columns["@toDate"] == "999912"), None)

        #県の直下で値が取得できなかった場合、
        #郡レベルでjsonを再取得
        if not muni_name:
            params = {"RegionCode": muni_cd}
            r = await client.get(self.REGION_INFO_URL, params=params)
            r.raise_for_status()
            data = r.json()
            objs = data["GET_META_REGION_INF"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]
            muni_name = next((c["@name"] for obj in objs for c in obj["CLASS"] if c["@regionCode"] == muni_cd and c["@toDate"] == "999912"), None)

            if not muni_name:
                print(f"値が取得できませんでした。muni_cd: {muni_cd}")
                return (None, prefecture_name)

        #ifの外でreturn(muni_nameが最初に取得できている時もこれで対応)
        return (muni_name, prefecture_name)

    async def fetch_stat_value(self, client: httpx.AsyncClient, stats_id: str, muni_cd: str, cat_code: str, date: str) -> float | None:
            """Fetch the value of a specific statistic from e-stat API"""
            year = date[:4]
            params = {
                 "appId": self.api_key,
                 "statsDataId": stats_id,
                 "cdArea": muni_cd,
                 "cdCat01": cat_code,
                 "time": year
            }
            r = await client.get(self.STATS_DATA_URL, params=params)
            r.raise_for_status()

            payload = r.json()["GET_STATS_DATA"]
            result = payload.get("RESULT", {})
            if result.get("STATUS") != 0:
                raise ValueError(
                    f"e-Stat API error: {result.get('ERROR_MSG', 'unknown error')}"
                )

            statistical_data = payload.get("STATISTICAL_DATA")
            if not statistical_data:
                raise ValueError("STATISTICAL_DATA is missing in e-Stat response")

            value = statistical_data["DATA_INF"]["VALUE"]

            if not value:
                print(f"値が取得できませんでした。stats_id: {stats_id}, muni_cd: {muni_cd}, cat_code: {cat_code}, date: {date}")
                return None
            
            #入力したyearの直近の国勢調査の人口or土地面積を取得（配列の最後が直近）
            return float(value[-1]["$"])
    
    async def fetch_population(self, client: httpx.AsyncClient, muni_cd: str, date: str) -> float | None:
        """Fetch the population value for a specific municipality code"""
        return await self.fetch_stat_value(client, self.STATS_DATA_ID, muni_cd, self.CAT_CODE_POPULATION, date)

    async def fetch_area(self, client: httpx.AsyncClient, muni_cd: str, date: str) -> float | None:
        """Fetch the area value for a specific municipality code"""
        return await self.fetch_stat_value(client, self.STATS_DATA_ID_2, muni_cd, self.CAT_CODE_AREA, date)