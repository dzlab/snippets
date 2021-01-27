# Sparkling Water

## How to build from source
The steps to build are:

* Download hadoop 3.3.0, unzip
* Create `HADOOP_HOME` pointing to hadoop directory
* Create `SPARK_DIST_CLASSPATH=((HADOOP_HOME/bin/hadoop classpath)`
* Download spark 2.4.7 without hadoop, unzip
* Create `SPARK_HOME` pointing to spark home
* Make sure can run `$SPARK_HOME/bin/spark-shell`
* Clone Sparkling water
* Build against scala 2.11 and spark 2.4 `./gradlew dist -Pspark=2.4 -PscalaBaseVersion=2.11`
