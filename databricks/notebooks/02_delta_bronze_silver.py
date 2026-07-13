# Silver layer — clean and deduplicate bronze data
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("bootcamp_silver").getOrCreate()
bronze = spark.table("bootcamp.bronze.raw_prices")

window = Window.partitionBy("symbol", "Date").orderBy(col("ingested_at").desc())

silver = bronze \
    .withColumn("rn", row_number().over(window)) \
    .filter(col("rn") == 1) \
    .drop("rn") \
    .filter(col("Close").isNotNull())

silver.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("bootcamp.silver.prices_clean")
