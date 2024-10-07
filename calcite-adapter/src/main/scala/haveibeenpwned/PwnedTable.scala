package haveibeenpwned

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import org.apache.calcite.DataContext
import org.apache.calcite.linq4j.{Enumerable, Linq4j}
import org.apache.calcite.rel.`type`.{RelDataType, RelDataTypeFactory}
import org.apache.calcite.schema.ScannableTable
import org.apache.calcite.schema.impl.AbstractTable
import org.apache.calcite.sql.`type`.SqlTypeName

import java.time.ZonedDateTime
import java.util.Date
import scala.collection.JavaConverters._

class PwnedTable(fetchData: () => Array[Map[String, AnyRef]], schema: Map[String, SqlTypeName]) extends AbstractTable with ScannableTable {

  override def getRowType(typeFactory: RelDataTypeFactory): RelDataType = {
    val (fieldNames, fieldTypes) = schema.unzip
    val types = fieldTypes.map(typeFactory.createSqlType).toList.asJava

    typeFactory.createStructType(types, fieldNames.toList.asJava)
  }

  override def scan(root: DataContext): Enumerable[Array[AnyRef]] = {
    val rows = fetchData().map{d =>
      val rowBuilder = Array.newBuilder[AnyRef]
      schema.foreach { case (n, t) =>
        val oldValue = d.getOrElse(n, null)
        val newValue = convertToSQLType(t, oldValue)
        rowBuilder += newValue
      }
      rowBuilder.result()
    }
    Linq4j.asEnumerable(rows)
  }

  def convertToSQLType(t: SqlTypeName, v: AnyRef): AnyRef = {
    Option(v) match {
      case None => v
      case Some(_) =>
        t match {
          case SqlTypeName.DATE =>
            java.sql.Date.valueOf(String.valueOf(v))
          case SqlTypeName.TIMESTAMP =>
            val instant = ZonedDateTime.parse(String.valueOf(v).seq)
            java.sql.Timestamp.valueOf(instant.toLocalDateTime)
          case _ => v
        }
    }
  }
}

object PwnedTable {
  case class Breach(Title: String, Name: String, Domain: String,
                    BreachDate: Date, AddedDate: Date, ModifiedDate: Date,
                    PwnCount: Int, Description: String, LogoPath: String, DataClasses: Array[String],
                    IsVerified: Boolean, IsFabricated: Boolean, IsSensitive: Boolean, IsActive: Boolean,
                    IsRetired: Boolean, IsSpamList: Boolean, IsMalware: Boolean, IsSubscriptionFree: Boolean)

  // create schema for breaches table
  def breaches(): PwnedTable = {
    val schema = Map(
      "Title" -> SqlTypeName.VARCHAR,
      "Name" -> SqlTypeName.VARCHAR,
      "Domain" -> SqlTypeName.VARCHAR,
      "BreachDate" -> SqlTypeName.DATE,
      "AddedDate" -> SqlTypeName.TIMESTAMP,
      "PwnCount" -> SqlTypeName.INTEGER,
      "Description" -> SqlTypeName.VARCHAR,
      "IsVerified" -> SqlTypeName.BOOLEAN,
      "IsSensitive" -> SqlTypeName.BOOLEAN,
      "IsRetired" -> SqlTypeName.BOOLEAN)
    new PwnedTable(fetch("breaches"), schema)
  }

  private def fetch(tableName: String)(): Array[Map[String, AnyRef]] = {
    val mapper = new ObjectMapper()
    mapper.registerModule(DefaultScalaModule)
    val url = s"https://haveibeenpwned.com/api/v2/$tableName"
    val resp = scala.io.Source.fromURL(url)
    val body = resp.mkString
    mapper.readValue(body, classOf[Array[Map[String, AnyRef]]])
  }
}