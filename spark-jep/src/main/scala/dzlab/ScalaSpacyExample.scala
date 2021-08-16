package dzlab

import java.io.File
import jep.Jep

object ScalaSpacyExample extends App {

  val jep = new Jep(false, new File(".").getPath())
  jep.runScript("src/main/python/spacy_ner.py")

  val text = "The red fox jumped over the lazy dog."

  // Evaluation method 1
  jep.eval(s"result = ner('$text')")
  val res1 = jep.getValue("result")
  println(Utils.prettify(res1))

  // Evaluation method 2
  val res2 = jep.invoke("ner", text.asInstanceOf[AnyRef])
  println(Utils.prettify(res2))
}