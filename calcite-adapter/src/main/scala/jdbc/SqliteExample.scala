package jdbc

import org.apache.calcite.adapter.jdbc.JdbcSchema
import org.apache.calcite.avatica.util.Casing
import org.apache.calcite.config.CalciteConnectionProperty
import org.apache.calcite.jdbc.CalciteConnection
import org.apache.calcite.schema.Schema

import java.sql.{Connection, DriverManager, SQLException}
import java.util.{HashMap, Map, Properties}
import scala.collection.convert.ImplicitConversions.`set asScala`


object SqliteExample {
  def main(args: Array[String]): Unit = {
    insert()
    query(DriverManager.getConnection("jdbc:sqlite:sample.db"), "person")
    val props = new Properties
    props.setProperty(CalciteConnectionProperty.FUN.camelName(), "postgresql")
    props.setProperty(CalciteConnectionProperty.CASE_SENSITIVE.camelName(), "false")
    props.setProperty(CalciteConnectionProperty.QUOTED_CASING.camelName(), Casing.UNCHANGED.name)
    props.setProperty(CalciteConnectionProperty.UNQUOTED_CASING.camelName(), Casing.UNCHANGED.name)
    props.setProperty(CalciteConnectionProperty.CASE_SENSITIVE.camelName(), "false")
    val connection = DriverManager.getConnection("jdbc:calcite:", props)
    val calciteConnection = connection.unwrap(classOf[CalciteConnection])

    val rootSchema = calciteConnection.getRootSchema

    val operand: Map[String, AnyRef] = new HashMap[String, AnyRef]()
    operand.put("jdbcUrl", "jdbc:sqlite:sample.db")

    rootSchema.add("lt", JdbcSchema.Factory.INSTANCE.create(rootSchema, "lt", operand))

    // set default schema so we don't have to prefix table names
    calciteConnection.setSchema("lt")

    // List all available schemas and their tables
    print("root", rootSchema)

    query(calciteConnection, "person")
  }

  def print(name: String, schema: Schema): Unit = {
    println(s"[Schema: $name]")
    println("Available tables: "+schema.getTableNames)
    println("Available schemas: "+schema.getSubSchemaNames)
    schema.getSubSchemaNames().map(name => print(name, schema.getSubSchema(name)))
  }

  def query(connection: Connection, table: String): Unit = {
    val statement = connection.createStatement()
    val rs = statement.executeQuery(s"select * from $table")
    while (rs.next()) {
      // read the result set
      System.out.println("name = " + rs.getString("name"))
      System.out.println("id = " + rs.getInt("id"))
    }
  }

  def insert(): Unit = {
    // create a database connection
    val connection = DriverManager.getConnection("jdbc:sqlite:sample.db")
    val statement = connection.createStatement()

    try {
      // set timeout to 30 sec.
      statement.setQueryTimeout(30)
      // run queries
      statement.executeUpdate("drop table if exists person")
      statement.executeUpdate("create table person (id integer, name string)")
      statement.executeUpdate("insert into person values(1, 'leo')")
      statement.executeUpdate("insert into person values(2, 'yui')")
      // close connection
      statement.close()
      connection.close()
    }
    catch {
      case e: SQLException =>
        // if the error message is "out of memory", it probably means no database file is found
        e.printStackTrace(System.err);
    }
  }
}

