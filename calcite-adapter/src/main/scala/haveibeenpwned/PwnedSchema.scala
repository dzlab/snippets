package haveibeenpwned

import org.apache.calcite.schema.Table
import org.apache.calcite.schema.impl.AbstractSchema

import java.util
import java.util.Collections

class PwnedSchema extends AbstractSchema {

  override def getTableMap: util.Map[String, Table] = {
    Collections.singletonMap("breaches", PwnedTable.breaches())
  }

}
