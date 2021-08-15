package dzlab

import java.util.ArrayList
import jep.Jep

object ScalaSpacyExample extends App {

  val jep = new Jep()
  jep.runScript("src/main/python/spacy_ner.py")

  val text = "The red fox jumped over the lazy dog."

  // Evaluation method 1
  jep.eval(s"result = ner('$text')")
  val ans1 = jep.getValue("result")
  println(ans1.asInstanceOf[ArrayList[ArrayList[String]]])

  // Evaluation method 2
  val ans2 = jep.invoke("ner", text.asInstanceOf[AnyRef])
  println(ans2.asInstanceOf[ArrayList[ArrayList[String]]])
}