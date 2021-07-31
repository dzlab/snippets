package dz.lab

import ai.h2o.sparkling.H2OContext
import ai.h2o.sparkling.ml.algos.H2OGBM
import org.apache.spark.sql.functions._

/**
 * Example of Sparkling Water based application.
 */
object SparklingWaterDroplet {

  def main(args: Array[String]) {
    val spark = Spark.sparkSession

    // Create H2O Context
    val h2oContext = H2OContext.getOrCreate()

    val irisTable = spark.read.option("header", "true").option("inferSchema", "true").csv("/tmp/iris.csv")

    // Build GBM model
    val model = new H2OGBM()
      .setLabelCol("class")
      .setNtrees(5)
      .fit(irisTable)

    // Make prediction on train data
    val predictions = model.transform(irisTable)

    // Compute number of miss-predictions with help of Spark API

    // Make sure that both DataFrames has the same number of elements
    assert(irisTable.count() == predictions.count)
    val irisTableWithId = irisTable.select("class").withColumn("id", monotonically_increasing_id())
    val predictionsWithId = predictions.select("prediction").withColumn("id", monotonically_increasing_id())
    val df = irisTableWithId.join(predictionsWithId, "id").drop("id")
    val missPredictions = df.filter(df("class") =!= df("prediction"))
    val numMissPredictions = missPredictions.count()

    println(
      s"""
         |Number of miss-predictions: $numMissPredictions
         |
         |Miss-predictions:
         |
         |actual X predicted
         |------------------
         |${missPredictions.collect().mkString("\n")}
       """.stripMargin
    )

    scala.io.StdIn.readLine()
    // Shutdown application
    h2oContext.stop(true)
  }
}
