package dzlab

import collection.JavaConverters._
import java.util.ArrayList
import jep.{Jep, SharedInterpreter}
import org.apache.spark.{SparkConf, SparkContext}

object SparkNltkExample extends App {

  val conf = new SparkConf()
    .setAppName("Spark Job")
    .setIfMissing("spark.master", "local[*]")

  val sc = new SparkContext(conf)

  val textFile = sc.textFile("data/title_StackOverflow.txt")

  // Evaluation method 1
  // val resultRDD1 = textFile.mapPartitions{input =>
  //   val jep = new SharedInterpreter()
  //   val scriptFile = "src/main/python/nltk_ner.py"
  //   val script = scala.io.Source.fromFile(scriptFile).mkString
  //   jep.exec(script)
  //   val output = input.map(text=>{
  //     jep.eval(s"result = nltk_lemmatizer('$text')")
  //     val result = jep.getValue("result")
  //     Utils.prettify(result)
  //   })
  //   output
  // }
  // println(resultRDD1.collect().mkString("\n"))

  // Evaluation method 2
  val resultRDD2 = textFile.mapPartitions{input =>
    val jep = new SharedInterpreter()
    jep.runScript("src/main/python/nltk_ner.py")
    val output = input.map(text=>{
      val result = jep.invoke("nltk_lemmatizer", text.asInstanceOf[AnyRef])
      Utils.prettify(result)
    })
    output
  }

  println(resultRDD2.collect().mkString("\n"))

}