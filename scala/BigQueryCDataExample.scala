import java.sql._
import java.util.Properties

import org.scalatest.{FlatSpec, Matchers}
import org.scalatest.mockito.MockitoSugar

class BigQueryApp extends FlatSpec with Matchers with MockitoSugar {

  val prop = new Properties();
  prop.setProperty("AuthScheme","OAuth");
  prop.setProperty("InitiateOAuth","REFRESH");
  prop.setProperty("OAuthClientId","");
  prop.setProperty("OAuthClientSecret","");
  prop.setProperty("OAuthAccessToken","");
  prop.setProperty("OAuthRefreshToken","");
  prop.setProperty("ProjectId","");
  prop.setProperty("DatasetId","");


  val conn: Connection =
    try {
      DriverManager.getConnection("jdbc:googlebigquery:",prop);
    } catch {
      case se: SQLException =>
        System.err.println(se.getMessage());
        throw se;
    }

  val query = "SELECT * FROM datasetId.table LIMIT 100";

  val result = conn.createStatement().execute(query)
  println(result)

}
