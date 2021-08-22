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

  // Evaluation method 1
  val resultRDD1 = textFile.mapPartitions{input =>
    val jep = new Jep()
    val scriptFile = "src/main/python/spacy_ner.py"
    val script = scala.io.Source.fromFile(scriptFile).mkString
    jep.setInteractive(true)
    jep.eval(script)
    jep.setInteractive(false)
    val output = input.map(text=>{
      jep.eval(s"result = ner('$text')")
      val result = jep.getValue("result")
      Utils.prettify(result)
    })
    jep.close()
    output
  }
  println(resultRDD1.collect().mkString("\n"))

  // Evaluation method 2
  val resultRDD2 = textFile.mapPartitions{input =>
    val jep = new Jep()
    jep.runScript("src/main/python/spacy_ner.py")
    val output = input.map(text=>{
      val result = jep.invoke("ner", text.asInstanceOf[AnyRef])
      Utils.prettify(result)
    })
    jep.close()
    output
  }

  println(resultRDD2.collect().mkString("\n"))

}