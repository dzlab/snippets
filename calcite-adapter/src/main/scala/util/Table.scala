package util

case class TableRow(cells: Seq[String])

class Table(headers: Seq[String], rows: Seq[TableRow]) {
  private val columnWidths = headers.zip(headers.indices.map(i =>
    (headers(i) +: rows.map(_.cells(i))).map(_.length).max
  )).toMap

  private def formatRow(row: Seq[String]): String =
    row.zip(headers).map { case (cell, header) =>
      cell.padTo(columnWidths(header), ' ')
    }.mkString("| ", " | ", " |")

  def print(): Unit = {
    val separator = headers.map(h => "-" * columnWidths(h)).mkString("+", "+", "+")
    println(separator)
    println(formatRow(headers))
    println(separator)
    rows.foreach(row => println(formatRow(row.cells)))
    println(separator)
  }
}
