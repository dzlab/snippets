/**
 * Example starting an HTTP server using Akka
 */

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.model.{ContentType, ContentTypes, HttpEntity, HttpResponse}
import org.scalatest.BeforeAndAfterAll
import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.unmarshalling.Unmarshal
import akka.stream.ActorMaterializer
import akka.util.ByteString
import org.apache.commons.lang.exception.ExceptionUtils
import play.api.libs.json.Json
import scala.util.{Failure, Success, Try}

import scala.concurrent.Await
import scala.concurrent.ExecutionContext.Implicits.global

object App {
  def startServer(): Unit = {
    // bring up local web server for hosting files that REST nodes can access via a REST API
    val port = Config.vadServerPort.toInt
    implicit val actorSystem: ActorSystem = system
    implicit val materializer: ActorMaterializer = ActorMaterializer()

    val routes = get {
      path("fileServer") {
        parameters('filePath.as[String]) { filePath =>
          val content =
            try {
              TestUtils.resourceFile(s"/fileServer/$filePath").mkString
            } catch {
              case _: Exception => "{ \"error\": \"File " + filePath + " not found \" }"
            }
          complete(HttpResponse(
            entity = HttpEntity.Strict(ContentTypes.`application/json`, ByteString.fromString(content))
          ))
        }
      }
    } ~ {
      post { // Echo endpoint that returns request body
        extractRequestContext { requestContext =>
          path("echo") {
            requestContext.request.entity.contentType match {
              case ContentTypes.`application/json` => {
                onComplete (Unmarshal(requestContext.request.entity).to[String]) {
                  case Success(value) => {
                    val body = Try(Json.parse(value)) match {
                      case Success(_) => ByteString.fromString(value)
                      case Failure(e) =>
                        ByteString.fromString(s"""{"error": "Received malformed json request", "cause": "${ExceptionUtils.getFullStackTrace(e)}""")
                    }
                    complete(HttpResponse(
                      entity = HttpEntity.Strict(ContentTypes.`application/json`, body)
                    ))
                  }
                  case Failure(e) => complete(s"""{ "error": "Expected HTTP request with JSON body" }""")
                }
              }
              case x: ContentType => complete(s"""{ "error": "Unhandled content-type $x" }""")
            }
          }
        }
      }
    }

    val bindFuture = Http().bindAndHandle(
      handler   = routes,
      interface = "0.0.0.0",
      port      = port
    )
    println(s"VAD listening on port $port")

    // shutdown VAD if we cant bind to 10011
    val res = Await.ready(bindFuture, Utils.defaultTimeout.duration)
    res
      .onComplete({
        case Failure(e) =>
          e.printStackTrace()
          System.exit(-1)
        case _ =>
      })
  }
}
