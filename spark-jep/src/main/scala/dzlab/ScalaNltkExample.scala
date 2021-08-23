package dzlab

import java.io.File
import jep.Jep

object ScalaNltkExample extends App {

  val jep = new Jep(false, new File(".").getPath())
  jep.runScript("src/main/python/nltk_ner.py")

  val text = "The red fox jumped over the lazy dog."

  // Evaluation method 1
  jep.eval(s"result = nltk_lemmatizer('$text')")
  val res1 = jep.getValue("result")
  println(Utils.prettify(res1))

  // Evaluation method 2
  val res2 = jep.invoke("nltk_lemmatizer", text.asInstanceOf[AnyRef])
  println(Utils.prettify(res2))
}