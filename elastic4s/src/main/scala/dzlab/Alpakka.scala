package dzlab

import better.files.Resource
import akka.actor.ActorSystem
import akka.stream.ActorMaterializer
import akka.stream.scaladsl.Sink
import akka.stream.scaladsl.Source
import akka.util.ByteString
import org.apache.http.HttpHost
import org.elasticsearch.client.RestClient

import akka.stream.alpakka.elasticsearch.ElasticsearchWriteSettings
import akka.stream.alpakka.elasticsearch.RetryAtFixedRate
import akka.stream.alpakka.elasticsearch.WriteMessage
import akka.stream.alpakka.elasticsearch.scaladsl.ElasticsearchFlow

import akka.stream.alpakka.csv.scaladsl.CsvParsing

import scala.concurrent.Await
import scala.concurrent.duration._
import spray.json._
import DefaultJsonProtocol._

case class Iris(label: String, f1: Double, f2: Double, f3: Double, f4: Double)

object ElasticAlpakka extends App {
  println("Hello world!")
  
  implicit val format: JsonFormat[Iris] = jsonFormat5(Iris)
  // initialize the Akka system
  implicit val actorSystem = ActorSystem()
  implicit val actorMaterializer = ActorMaterializer()
  implicit val executor = actorSystem.dispatcher
  
  // initialize the Elasticsearch client
  implicit val client: RestClient = RestClient.builder(new HttpHost("0.0.0.0", 9200)).build()

  // initializing the sink with back pressure and retry logic
  val sinkSettings = ElasticsearchWriteSettings()
    .withBufferSize(1000)
    .withVersionType("internal")
    .withRetryLogic(RetryAtFixedRate(maxRetries = 5, retryInterval = 1.second))

  // create a pipeline with CSV source, for every line, create a Iris Index message and will ingest in an index iris- alpakka using the Elasticsearch Sink
  val graph = Source.single(ByteString(Resource.getAsString("iris.csv")))
    .via(CsvParsing.lineScanner())
    .drop(1)
    .map(values => WriteMessage.createIndexMessage[Iris](
      Iris(values(5).utf8String, values.head.utf8String.toDouble, values(1).utf8String.toDouble, values(2).utf8String.toDouble, values(3).utf8String.toDouble))
    )
    .via(ElasticsearchFlow.create[Iris]("iris-alpakka", "_doc", settings = sinkSettings))
    .runWith(Sink.ignore)

  // wait for the pipeline to finish
  val finish = Await.result(graph, Duration.Inf)
  client.close()
  actorSystem.terminate()
  Await.result(actorSystem.whenTerminated, Duration.Inf)
}
