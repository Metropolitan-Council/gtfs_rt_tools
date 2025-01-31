# contains functions to write data to various file formats
from pyspark.sql import DataFrame

def write_csv(df, output_path):
    df.to_csv(output_path, index=False)
