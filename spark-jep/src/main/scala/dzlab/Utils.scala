package dzlab

import collection.JavaConverters._
import java.util.ArrayList

object Utils {

  def prettify(input: Object): String = {
    input.asInstanceOf[ArrayList[Object]].asScala
      .map(_.asInstanceOf[java.util.List[String]].asScala.mkString(","))
      .mkString("|")
  }
}