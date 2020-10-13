scalaVersion := "2.12.0"

name := "Elastic scala"
version := "1.0"

val alpakkaVersion = "2.0.2"
val akkaVersion = "2.5.31"

val alpakkaLibs = Seq(
  "com.lightbend.akka" %% "akka-stream-alpakka-csv" % alpakkaVersion,
  "com.lightbend.akka" %% "akka-stream-alpakka-elasticsearch" % alpakkaVersion,
  "com.typesafe.akka" %% "akka-stream" % akkaVersion
)

val miscLibs = Seq(
  "io.spray" %%  "spray-json" % "1.3.5",
  "com.github.pathikrit" %% "better-files" % "3.9.1"
)

libraryDependencies ++= alpakkaLibs ++ miscLibs
