from pathlib import Path

import pandas as pd


class PipelineIO:
    BASE_DIR = Path(__file__).resolve().parent.parent #datapipeline
    INPUT_PATH = BASE_DIR / "data_csv" / "input.csv"
    OUTPUT_PATH = BASE_DIR / "./data_csv" "/output.csv"
    
    def __init__(self) -> None:
        self.input_path = Path(self.INPUT_PATH)
        self.output_path = Path(self.OUTPUT_PATH)

        """Check inputfile existence and output directory existence."""
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {self.input_path}")
            
        if not self.output_path.parent.exists():
            raise FileNotFoundError(f"Output directory does not exist: {self.output_path.parent}")
        print(self.INPUT_PATH)

    def read_csv(self) -> pd.DataFrame:
        """Read a CSV file and return a DataFrame."""
        df = pd.read_csv(self.input_path)
        return df

    def write_csv(self, df: pd.DataFrame) -> None:
        """Write a DataFrame to a CSV file."""
        df.to_csv(self.output_path, index=False)

    
    