package dzlab

import collection.JavaConverters._
import java.util.ArrayList
import jep.Jep
import org.apache.spark.{SparkConf, SparkContext}

object SparkSpacyExample extends App {

  val conf = new SparkConf()
    .setAppName("Spark Job")
    .setIfMissing("spark.master", "local[*]")

  val sc = new SparkContext(conf)

  val textFile = sc.textFile("data/title_StackOverflow.txt")

  val resultRDD = textFile.mapPartitions{iterator =>
    val jep = new Jep()
    jep.runScript("src/main/python/spacy_ner.py")
    iterator.map(text=>{
      val result = jep.invoke("ner", text.asInstanceOf[AnyRef])
      result.asInstanceOf[ArrayList[ArrayList[String]]].asScala
        .map(_.asScala.mkString(","))
        .mkString("|")
    })
  }

  println(resultRDD.collect().mkString("\n"))

}