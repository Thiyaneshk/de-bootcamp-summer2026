# Databricks notebook — Bronze layer ingestion
# Run via: databricks jobs run-now --job-id <id>
import pandas as pd
import yfinance as yf
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

spark = SparkSession.builder.appName("bootcamp_ingest").getOrCreate()

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]

dfs = []
for symbol in SYMBOLS:
    df = yf.download(symbol, period="2y", interval="1d")
    df["symbol"] = symbol
    df = df.reset_index()
    dfs.append(df)

pandas_df = pd.concat(dfs)
spark_df = spark.createDataFrame(pandas_df) \
    .withColumn("ingested_at", current_timestamp()) \
    .withColumn("source", lit("yfinance"))

spark_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable("bootcamp.bronze.raw_prices")
