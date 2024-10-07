package haveibeenpwned

import org.apache.calcite.config.Lex
import org.apache.calcite.jdbc.CalciteConnection

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

    while (rs.next) {
      val count = rs.getLong("PwnCount")
      val name = rs.getString("Name")
      val domain = rs.getString("Domain")
      val breach = rs.getDate("BreachDate")
      val added = rs.getTimestamp("AddedDate")
      println("name: " + name + "; count: " + count + "; domain: " + domain + "; breach: " + breach + "; added: " + added)
    }
    rs.close()
    statement.close()

//    // Create the query planner with sales schema. conneciton.getSchema returns default schema name specified in sales.json
//    val queryPlanner = new SimpleQueryPlanner(schema);
//    RelNode loginalPlan = queryPlanner.getLogicalPlan("select product from orders");
//    System.out.println(RelOptUtil.toString(loginalPlan));

    connection.close()
  }
}
