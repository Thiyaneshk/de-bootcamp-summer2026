# Feature engineering for Gold layer (e.g. Technical indicators)
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("bootcamp_gold").getOrCreate()
silver = spark.table("bootcamp.silver.prices_clean")

window_spec_20 = Window.partitionBy("symbol").orderBy("Date").rowsBetween(-19, 0)
window_spec_50 = Window.partitionBy("symbol").orderBy("Date").rowsBetween(-49, 0)

gold = silver \
    .withColumn("sma_20", avg(col("Close")).over(window_spec_20)) \
    .withColumn("sma_50", avg(col("Close")).over(window_spec_50))

gold.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("bootcamp.gold.features")
