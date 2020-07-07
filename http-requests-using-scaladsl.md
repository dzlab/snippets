# Client-Side HTTP Requests using ScalaDSL

interact with APIs. Unfortunately, there are few resources out there to guide you on how to use the HTTP client scaladsl library for Akka HTTP to make these requests. I had a hard time finding a good resource on this topic and was struggling to create a simple REST API consumer for our Microshare™ platform. Of course, the scala akka documentation does exist and it is a great reference but sometimes it gets confusing.

Without a clear guide, it is tempting to simply load the Apache HTTPClient Java libraries and follow the well-worn path. Resist! The Akka HTTP scaladsl allows for the plumbing necessary for a reactive solution such as managing back-pressure for downstream consumers. This post will help you learn how to use this library in small simple steps.

Step 1: First of all you need to import some parts of this library.
```scala
import akka.http.scaladsl.Http

import akka.http.scaladsl.model._
```
Step 2: Build your HTTP request by providing some details for the request including the method (type of the call – GET or POST), the url (any endpoint as string), the protocol (usually HTTP/1.1).

GET HTTP request:
```scala
val HttpRequest_get = HttpRequest(method = HttpMethods.GET, uri = url, protocol = HttpProtocols.`HTTP/1.1`)
```
POST HTTP request:
```scala
var HttpRequest_post = HttpRequest(method = HttpMethods.POST, uri = url, protocol = HttpProtocols.`HTTP/1.1`)
```
Step 3: Add authorization to your request depending on the authentication/authorization type you are trying to use.

For OAUTH2 type authentication:

GET
```scala
val requestWithAuth: HttpRequest = HttpRequest_get.addHeader(Authorization(OAuth2BearerToken(“the-token”)))
```
POST
```scala
val requestWithAuth: HttpRequest = HttpRequest_post.addHeader(Authorization(OAuth2BearerToken(“the-token”)))
```
For BASIC type authentication:

GET
```scala
val requestWithAuth: HttpRequest = HttpRequest_get.addHeader(Authorization(BasicHttpCredentials(“username”, “password”)))
```
POST
```scala
val requestWithAuth: HttpRequest = HttpRequest_post.addHeader(Authorization(BasicHttpCredentials(“username”, “password”)))
```
For API type authentication:

To do calls using api key, just pass the api key information in your url as parameters, for example, url=“https://example.com?apikey=”

Step 4: Add Accept Response Header to your GET request in order to get a specific type or format (for example application/xml) of the response for your GET call. (If you are only trying to do a simple GET call without specifying the type or format of the response, you can skip this step.)

GET

To get the response of type application/json:
```scala
val requestWithAcceptResponseHeader: HttpRequest =

requestWithAuth.addHeader(Accept(MediaTypes.`application/json`))
```
To get the response of type application/xml:
```scala
val requestWithAcceptResponseHeader: HttpRequest =

requestWithAuth.addHeader(Accept(MediaTypes.`application/xml`))
```
To get the response of type text/plain:
```scala
val requestWithAcceptResponseHeader: HttpRequest =

requestWithAuth.addHeader(Accept(MediaTypes.`text/plain`))
```
To get the response of type text/xml:
```scala
val requestWithAcceptResponseHeader: HttpRequest =

requestWithAuth.addHeader(Accept(MediaTypes.`text/xml`))
```
To get the response of type text/csv:
```scala
val requestWithAcceptResponseHeader: HttpRequest =

requestWithAuth.addHeader(Accept(MediaTypes.`text/csv`))
```
To get the response of type text/html:
```scala
val requestWithAcceptResponseHeader: HttpRequest =

requestWithAuth.addHeader(Accept(MediaTypes.`text/html`))
```
Step 5: Add Entity (data and its content type) to your POST request. The entity is required for your POST call. An entity includes both the body/data to be posted with your POST call and the format of that data also known as content type of the data. Note that the data/body needs to be passed in as byte string format for the request. You can convert the string data/body into byte string format using:
```scala
val body = “abcd”

val data = ByteString(body)
```
You will need to import akka.util.ByteString to do this.

POST

To post the data with content type. Note that some of the content types require you to pass the charset also while others do not.

To post the data with content type application/json:
```scala
val requestWithBodyAndContentType: HttpRequest = requestWithAuth.withEntity(HttpEntity.Strict(ContentType(MediaTypes.`application/json`), data))
```
To post the data with content type application/xml:
```scala
val requestWithBodyAndContentType: HttpRequest =
requestWithAuth.withEntity(HttpEntity.Strict(ContentType.WithCharset(MediaTypes.`application/xml`, HttpCharsets.`UTF-8`), data))
```
To post the data with content type text/plain:
```scala
val requestWithBodyAndContentType: HttpRequest = requestWithAuth.withEntity(HttpEntity.Strict(ContentType.WithCharset(MediaTypes.`text/plain`, HttpCharsets.`UTF-8`), data))
```
To post the data with content type text/xml:
```scala
val requestWithBodyAndContentType: HttpRequest = requestWithAuth.withEntity(HttpEntity.Strict(ContentType.WithCharset(MediaTypes.`text/xml`, HttpCharsets.`UTF-8`), data))
```
To post the data with content type text/csv:
```scala
val requestWithBodyAndContentType: HttpRequest = requestWithAuth.withEntity(HttpEntity.Strict(ContentType.WithCharset(MediaTypes.`text/csv`, HttpCharsets.`UTF-8`), data))
```
To post the data with content type text/html:
```scala
val requestWithBodyAndContentType: HttpRequest = requestWithAuth.withEntity(HttpEntity.Strict(ContentType.WithCharset(MediaTypes.`text/csv`, HttpCharsets.`UTF-8`), data))
```
