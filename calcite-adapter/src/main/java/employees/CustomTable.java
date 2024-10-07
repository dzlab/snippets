package employees;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
//import commons.StreamIterable;
import org.apache.calcite.DataContext;
import org.apache.calcite.linq4j.Enumerable;
import org.apache.calcite.linq4j.Linq4j;
import org.apache.calcite.rel.type.RelDataType;
import org.apache.calcite.rel.type.RelDataTypeFactory;
import org.apache.calcite.schema.ScannableTable;
import org.apache.calcite.schema.impl.AbstractTable;
import org.apache.calcite.sql.type.SqlTypeName;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class CustomTable extends AbstractTable implements ScannableTable {

    private final Map<Object, ObjectNode> data;

    private final List<String> fieldNames;

    private final List<SqlTypeName> fieldTypes;

    public CustomTable(Map<Object, ObjectNode> data) {

        this.data = data;

        List<String> names = new ArrayList<>();
        names.add("id");
        names.add("name");
        names.add("age");
        this.fieldNames = names;

        List<SqlTypeName> types = new ArrayList<>();
        types.add(SqlTypeName.BIGINT);
        types.add(SqlTypeName.VARCHAR);
        types.add(SqlTypeName.INTEGER);
        this.fieldTypes = types;
    }

    @Override
    public RelDataType getRowType(RelDataTypeFactory typeFactory) {

        // https://github.com/apache/calcite/blob/fa8349069d141d3c75bafa06d5fb8800711ec8d6/example/csv/src/main/java/org/apache/calcite/adapter/csv/CsvEnumerator.java#L111

        List<RelDataType> types = fieldTypes.stream().map(typeFactory::createSqlType).collect(Collectors.toList());
        return typeFactory.createStructType(types, fieldNames);
    }

    @Override
    public Enumerable<Object[]> scan(DataContext root) {
        Stream<Object[]> dataStream = data.entrySet().stream().map(this::toObjectArray);
        return Linq4j.asEnumerable(new StreamIterable<>(dataStream));
    }

    private Object[] toObjectArray(Map.Entry<Object, ObjectNode> item) {

        Object[] res = new Object[fieldNames.size()];
        res[0] = item.getKey();

        for (int i = 1; i < fieldNames.size(); i++) {
            JsonNode v = item.getValue().get(fieldNames.get(i));
            SqlTypeName type = fieldTypes.get(i);
            switch (type) {
                case VARCHAR:
                    res[i] = v.textValue();
                    break;
                case INTEGER:
                    res[i] = v.intValue();
                    break;
                default:
                    throw new RuntimeException("unsupported sql type: " + type);
            }
        }
        return res;
    }
}
