import asyncio

import httpx
import pandas as pd
from tqdm.asyncio import tqdm

from datapipeline.dataIo.pipeline_io import PipelineIO

from .row_enricher import RowEnricher


class DataPipelineService:

    def __init__(self, chunk_size: int = 100, max_retries: int = 3,
                 request_timeout: int = 30) -> None:

        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        

    async def run(self) -> pd.DataFrame:
        # データパイプラインの処理を実行する
        print("データパイプラインの処理を開始します。")
        
        Io = PipelineIO()
        df = Io.read_csv()
        df = self.prepare_input(df)
        df = await self.run_latlon_enrichment(df)
        df = await self.run_municd_enrichment(df)
        #人口密度を算出(e-statの土地面積はha単位なので最後に100を掛ける)
        df['population_density'] = (df['population'] / df['area']) * 100
        # データフレームの列を整理
        df = df[['lat','lon','date','elevation','municd','muniname','prefecture','population','area','population_density','targetVal']]
        Io.write_csv(df)
        print("データパイプラインの処理が完了しました。")

        print(df)
        return df
        
        #後続の処理を書く

    def prepare_input(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare the input DataFrame by initializing necessary columns."""

        #データフレームを初期化(不要な列が存在しないようにする)
        #municd, elevationの列を初期化
        df = df[["lat", "lon", "date", "targetVal"]].copy()
        df["municd"] = None
        df["elevation"] = None
        df["muniname"] = None
        df["prefecture"] = None
        df["population"] = None
        df["area"] = None
        return df



    async def _process_in_chunks(self, df: pd.DataFrame, process_func) -> list[dict[str, object]]:
        results = []

        for i in range(0, len(df), self.chunk_size):
            chunk = df.iloc[i : i + self.chunk_size]
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                tasks = [process_func(client, row) for _, row in chunk.iterrows()]
                buffer = await tqdm.gather(*tasks, desc=f"chunk {i//self.chunk_size + 1}")
                results.extend(buffer)
                await asyncio.sleep(1) # チャンクの合間にサーバーを休ませる

        return results


    async def run_latlon_enrichment(self, df: pd.DataFrame) -> pd.DataFrame:
        counter = 0
        row_enricher = RowEnricher(concurrency=3)

        while counter < self.max_retries:
            # municdが欠損している行だけを抽出
            # 初回は df 全体、2回目以降は失敗した行だけが対象になる
            target_index = df[df["municd"].isna()].index
            if len(target_index) == 0:
                print("全てのmunicdを取得完了しました。")
                break
            print(f"残り{len(target_index)}件のmunicd取得を開始します")

            retry_df = df.loc[target_index]

            enriched_rows = await self._process_in_chunks(retry_df,
                                                           row_enricher.enrich_latlon_row)
            result_df = pd.DataFrame(enriched_rows, index=target_index)
            df.update(result_df) # updateを使うと、indexが一致する場所だけ上書きしてくれます

            print(f"municd取得の試行回数: {counter + 1}")   
            if len(df[df["municd"].isna()]) > 0:
                print("一部失敗したため、3秒後にリトライします...")
                await asyncio.sleep(3)

            counter += 1
        return df

    async def run_municd_enrichment(self, df: pd.DataFrame) -> pd.DataFrame:
        counter = 0
        row_enricher = RowEnricher(concurrency=3)

        while counter < self.max_retries:
            target_index = df[df["muniname"].isna()].index
            if len(target_index) == 0:
                print("全てのmuninameを取得完了しました。")
                break

            print(f"残り{len(target_index)}件のmuniname取得を開始します")

            retry_df = df.loc[target_index]

            enriched_rows = await self._process_in_chunks(retry_df, row_enricher.enrich_municd_row)
            result_df = pd.DataFrame(enriched_rows, index=target_index)
            df.update(result_df)

            if len(df[df["muniname"].isna()]) > 0:
                print("一部失敗したため、3秒後にリトライします...")
                await asyncio.sleep(3)

            counter += 1

        return df



if __name__ == "__main__":
    service = DataPipelineService()
    try:
        df = asyncio.run(service.run())
    except FileNotFoundError as e:
        print(f"エラー: CSVファイルが見つかりません。 {e}")
  
