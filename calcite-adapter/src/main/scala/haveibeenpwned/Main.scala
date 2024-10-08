package haveibeenpwned

import org.apache.calcite.config.Lex
import org.apache.calcite.jdbc.CalciteConnection
import util.{Table, TableRow}

import java.sql.DriverManager
import java.util.Properties

object Main {

  def main(args: Array[String]): Unit = {
    Class.forName("org.apache.calcite.jdbc.Driver")

    System.setProperty("calcite.debug", "true") // CalciteSystemProperty.DEBUG
//    Hook.values().foreach(step =>
//      step.addThread(new Consumer[Any] {
//        override def accept(t: Any): Unit = {
//          println(s"# ${step.name()}:\n$t")
//          println((1 to 20).map("+"))
//        }
//      })
//    )

    val info = new Properties
    info.setProperty("lex", Lex.JAVA.name())
    val connection = DriverManager.getConnection("jdbc:calcite:", info)

    val calciteConnection = connection.unwrap(classOf[CalciteConnection])
    val rootSchema = calciteConnection.getRootSchema
    val schema = new PwnedSchema
    rootSchema.add("haveibeenpwned", schema)

    val statement = calciteConnection.createStatement
    val rs = statement.executeQuery(
      """
        |SELECT * FROM haveibeenpwned.breaches
        |WHERE Domain <> ''
        |ORDER BY PwnCount DESC
        |LIMIT 3
        |""".stripMargin)

    val rowsBuilder = Seq.newBuilder[TableRow]

    while (rs.next) {
      val count = rs.getLong("PwnCount")
      val name = rs.getString("Name")
      val domain = rs.getString("Domain")
      val breach = rs.getDate("BreachDate")
      val added = rs.getTimestamp("AddedDate")
      rowsBuilder += TableRow(Seq(name, String.valueOf(count), domain, String.valueOf(breach), String.valueOf(added)))
    }
    rs.close()
    statement.close()
    connection.close()

    val headers = Seq("name", "count", "domain", "breach", "added")
    val rows = rowsBuilder.result()

    val table = new Table(headers, rows)
    table.print()
  }
}
