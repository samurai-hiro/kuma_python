import asyncio
from pathlib import Path

import pandas as pd

from datapipeline.services import pipeline_service
from datapipeline.services.pipeline_service import DataPipelineService


async def _no_sleep(_seconds):
    return None


def test_prepare_input_keeps_required_columns_and_initializes_enrichment_fields():
    service = DataPipelineService()
    source = pd.DataFrame(
        {
            "lat": [35.0],
            "lon": [139.0],
            "date": ["2026-03-12"],
            "targetVal": [1],
            "unused": ["drop-me"],
        }
    )

    result = service.prepare_input(source)

    assert list(result.columns) == [
        "lat",
        "lon",
        "date",
        "targetVal",
        "municd",
        "elevation",
        "muniname",
        "prefecture",
        "population",
        "area",
    ]
    assert result.loc[0, "lat"] == 35.0
    assert result.loc[0, "lon"] == 139.0
    assert result.loc[0, "date"] == "2026-03-12"
    assert result.loc[0, "targetVal"] == 1
    assert result[["municd", "elevation", "muniname", "prefecture", "population", "area"]].isna().all().all()


def test_run_latlon_enrichment_retries_only_missing_rows(monkeypatch):
    monkeypatch.setattr(pipeline_service.asyncio, "sleep", _no_sleep)

    service = DataPipelineService(chunk_size=2, max_retries=3)
    source = service.prepare_input(
        pd.DataFrame(
            {
                "lat": [35.0, 36.0],
                "lon": [139.0, 140.0],
                "date": ["2026-03-12", "2026-03-13"],
                "targetVal": [1, 0],
            }
        )
    )

    call_indexes = []

    async def fake_process(retry_df, _process_func):
        call_indexes.append(retry_df.index.tolist())
        if len(call_indexes) == 1:
            return [
                {"municd": "001", "elevation": 10.5},
                {"municd": None, "elevation": None},
            ]
        return [{"municd": "002", "elevation": 20.5}]

    monkeypatch.setattr(service, "_process_in_chunks", fake_process)

    result = asyncio.run(service.run_latlon_enrichment(source))

    assert call_indexes == [[0, 1], [1]]
    assert result.loc[0, "municd"] == "001"
    assert result.loc[0, "elevation"] == 10.5
    assert result.loc[1, "municd"] == "002"
    assert result.loc[1, "elevation"] == 20.5


def test_run_municd_enrichment_updates_missing_rows(monkeypatch):
    monkeypatch.setattr(pipeline_service.asyncio, "sleep", _no_sleep)

    service = DataPipelineService(chunk_size=2, max_retries=2)
    source = service.prepare_input(
        pd.DataFrame(
            {
                "lat": [35.0, 36.0],
                "lon": [139.0, 140.0],
                "date": ["2026-03-12", "2026-03-13"],
                "targetVal": [1, 0],
            }
        )
    )
    source.loc[0, "municd"] = "001"
    source.loc[1, "municd"] = "002"

    call_indexes = []

    async def fake_process(retry_df, _process_func):
        call_indexes.append(retry_df.index.tolist())
        return [
            {
                "muniname": "A市",
                "prefecture": "A県",
                "population": 1000,
                "area": 50,
            },
            {
                "muniname": "B市",
                "prefecture": "B県",
                "population": 2000,
                "area": 100,
            },
        ]

    monkeypatch.setattr(service, "_process_in_chunks", fake_process)

    result = asyncio.run(service.run_municd_enrichment(source))

    assert call_indexes == [[0, 1]]
    assert result.loc[0, "muniname"] == "A市"
    assert result.loc[0, "prefecture"] == "A県"
    assert result.loc[0, "population"] == 1000
    assert result.loc[0, "area"] == 50
    assert result.loc[1, "muniname"] == "B市"
    assert result.loc[1, "prefecture"] == "B県"
    assert result.loc[1, "population"] == 2000
    assert result.loc[1, "area"] == 100


def test_run_builds_final_dataframe_and_writes_csv(monkeypatch):
    monkeypatch.setattr(pipeline_service.asyncio, "sleep", _no_sleep)

    input_df = pd.DataFrame(
        {
            "lat": [35.0],
            "lon": [139.0],
            "date": ["2026-03-12"],
            "targetVal": [7],
        }
    )
    written = {}

    class FakePipelineIO:
        def read_csv(self):
            return input_df.copy()

        def write_csv(self, df):
            written["df"] = df.copy()

    async def fake_run_latlon(df):
        df.loc[0, "municd"] = "13101"
        df.loc[0, "elevation"] = 12.0
        return df

    async def fake_run_municd(df):
        df.loc[0, "muniname"] = "千代田区"
        df.loc[0, "prefecture"] = "東京都"
        df.loc[0, "population"] = 5000
        df.loc[0, "area"] = 25
        return df

    monkeypatch.setattr(pipeline_service, "PipelineIO", FakePipelineIO)

    service = DataPipelineService()
    monkeypatch.setattr(service, "run_latlon_enrichment", fake_run_latlon)
    monkeypatch.setattr(service, "run_municd_enrichment", fake_run_municd)

    result = asyncio.run(service.run())

    assert list(result.columns) == [
        "lat",
        "lon",
        "date",
        "elevation",
        "municd",
        "muniname",
        "prefecture",
        "population",
        "area",
        "population_density",
        "targetVal",
    ]
    assert result.loc[0, "population_density"] == 20000
    assert "df" in written
    assert written["df"].equals(result)


def test_run_reads_input_csv_and_writes_output_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_service.asyncio, "sleep", _no_sleep)

    input_dir = tmp_path / "data_csv"
    input_dir.mkdir()
    input_path = input_dir / "input.csv"
    output_path = input_dir / "output.csv"

    pd.DataFrame(
        {
            "lat": [35.0],
            "lon": [139.0],
            "date": ["2026-03-12"],
            "targetVal": [7],
        }
    ).to_csv(input_path, index=False)

    monkeypatch.setattr(pipeline_service.PipelineIO, "INPUT_PATH", Path(input_path))
    monkeypatch.setattr(pipeline_service.PipelineIO, "OUTPUT_PATH", Path(output_path))

    async def fake_run_latlon(df):
        df.loc[0, "municd"] = 13101
        df.loc[0, "elevation"] = 12.0
        return df

    async def fake_run_municd(df):
        df.loc[0, "muniname"] = "千代田区"
        df.loc[0, "prefecture"] = "東京都"
        df.loc[0, "population"] = 5000
        df.loc[0, "area"] = 25
        return df

    service = DataPipelineService()
    monkeypatch.setattr(service, "run_latlon_enrichment", fake_run_latlon)
    monkeypatch.setattr(service, "run_municd_enrichment", fake_run_municd)

    result = asyncio.run(service.run())

    assert output_path.exists()

    written_df = pd.read_csv(output_path)
    expected_df = result.copy()
    # expected_df["municd"] = expected_df["municd"].astype(str)

    pd.testing.assert_frame_equal(written_df, expected_df, check_dtype=False)