```
// bin/sparkling-shell --conf "spark.executor.memory=1g"


import java.io.File
import ai.h2o.sparkling._
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.DataFrame
import org.apache.spark.sql.functions._
import org.apache.spark.sql.SparkSession
import ai.h2o.sparkling.ml.algos.H2OAutoML
import ai.h2o.sparkling.ml.models.H2OMOJOModel
import org.apache.spark.mllib.evaluation.RegressionMetrics

val hc = H2OContext.getOrCreate()
import spark.implicits._


// :paste
val weatherDataPath = "./examples/smalldata/chicago/Chicago_Ohare_International_Airport.csv"
val weatherDataFile = s"file://${new File(weatherDataPath).getAbsolutePath}"
val weatherTable = spark.read.option("header", "true").option("inferSchema", "true").csv(weatherDataFile).withColumn("Date", to_date(regexp_replace('Date, "(\\d+)/(\\d+)/(\\d+)", "$3-$2-$1"))).withColumn("Year", year('Date)).withColumn("Month", month('Date)).withColumn("DayofMonth", dayofmonth('Date))

val airlinesDataPath = "./examples/smalldata/airlines/allyears2k_headers.csv"
val airlinesDataFile = s"file://${new File(airlinesDataPath).getAbsolutePath}"
val airlinesTable = spark.read.option("header", "true").option("inferSchema", "true").option("nullValue", "NA").csv(airlinesDataFile)

val flightsToORD = airlinesTable.filter('Dest === "ORD")
val joined = flightsToORD.join(weatherTable, Seq("Year", "Month", "DayofMonth"))
val splits = joined.randomSplit(Array(.8, .2), 113)
val (trainDF, testDF) = (splits(0), splits(1))

case class AlgorithmParams(
                            featureCols: Array[String],
                            labelCol: String,
                            categoricalCols: Array[String],
                            splitRatio: Double = 0.8,
                            nFolds: Int = 5,
                            seed: Long = 12345L,
                            weightCol: String = null
                          )

case class AutoMLParams(
                         classSamplingFactors: Array[Float] = null,
                         convertInvalidNumbersToNa: Boolean = true,
                         convertUnknownCategoricalLevelsToNa: Boolean = true,
                         excludeAlgos: Array[String] = Array(),
                         foldCol: String = null,
                         ignoredCols: Array[String] = null,
                         maxAfterBalanceClasses: Float = 5.0f,
                         maxModels: Int = 10,
                         maxRuntimeSecs: Double = 0.0,
                         sortMetric: String = "AUTO",
                         stoppingMetric: String = "AUTO",
                         stoppingRounds: Int = 3,
                         stoppingTolerance: Double = -1.0
                       )

val featureColumnNames = trainDF.columns.filterNot(_.equals("ArrDelay"))
val targetColumnName = "ArrDelay"

val params = AlgorithmParams(
      featureCols = featureColumnNames,
      labelCol = targetColumnName,
	  categoricalCols = Array(),
      nFolds = 0)
val autoMLParams = AutoMLParams(excludeAlgos=Array("DeepLearning"))

def createAutoML(params: AlgorithmParams, autoMLParams: AutoMLParams): H2OAutoML = {
  new H2OAutoML()
        .setFeaturesCols(params.featureCols)
        .setLabelCol(params.labelCol)
        .setColumnsToCategorical(params.categoricalCols)
        .setSplitRatio(params.splitRatio)
        .setWithDetailedPredictionCol(true)
        .setNfolds(params.nFolds)
        .setSeed(params.seed)
        .setWeightCol(params.weightCol)
        .setMaxModels(autoMLParams.maxModels)
        .setClassSamplingFactors(autoMLParams.classSamplingFactors)
        .setConvertInvalidNumbersToNa(autoMLParams.convertInvalidNumbersToNa)
        .setConvertUnknownCategoricalLevelsToNa(autoMLParams.convertUnknownCategoricalLevelsToNa)
        .setExcludeAlgos(autoMLParams.excludeAlgos)
        .setFoldCol(autoMLParams.foldCol)
        .setIgnoredCols(autoMLParams.ignoredCols)
        .setMaxAfterBalanceSize(autoMLParams.maxAfterBalanceClasses)
        .setMaxRuntimeSecs(autoMLParams.maxRuntimeSecs)
        .setSortMetric(autoMLParams.sortMetric)
        .setStoppingMetric(autoMLParams.stoppingMetric)
        .setStoppingRounds(autoMLParams.stoppingRounds)
        .setStoppingTolerance(autoMLParams.stoppingTolerance)
}

def getRegressionMetrics(model: H2OMOJOModel, dataset: DataFrame, labelCol: String): RegressionMetrics = {
  val results: DataFrame = model.transform(dataset)
  val rawPredictionsAndLabels: RDD[(Double, Double)] = results
    .withColumn("prediction", col("prediction").cast("Double"))
    .withColumn(s"$labelCol", col(s"$labelCol").cast("Double"))
    .select(col("prediction"), col(s"$labelCol"))
	.rdd.map(row => (row.getAs[Double]("prediction"), row.getAs[Double](s"$labelCol")))
  new RegressionMetrics(rawPredictionsAndLabels)
}

val automl = createAutoML(params, autoMLParams)
val model = automl.fit(trainDF)


val leaderboard = automl.getLeaderboard("ALL")
leaderboard.show

val metrics = getRegressionMetrics(model, testDF, targetColumnName)
metrics.r2



val splits = spark.read.option("header", "true").option("inferSchema", "true").csv("/Users/dzlab/Downloads/project8-node-69.csv").randomSplit(Array(.8, .2), 113)
val (trainDF, testDF) = (splits(0), splits(1))

val targetColumnName = "gross_sales"
val featureColumnNames = trainDF.columns.filterNot(_.equals(targetColumnName))

val params = AlgorithmParams(
      featureCols = featureColumnNames,
      labelCol = targetColumnName,
	  categoricalCols = Array(),
      nFolds = 0)
val autoMLParams = AutoMLParams(excludeAlgos=Array("DeepLearning"))
val automl = createAutoML(params, autoMLParams)
val model = automl.fit(trainDF)
val metrics = getRegressionMetrics(model, testDF, targetColumnName)
metrics.r2
```
