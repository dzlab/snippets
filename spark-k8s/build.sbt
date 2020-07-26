val sparkVersion = "2.4.5"

scalaVersion in ThisBuild := "2.12.0"


val sparkLibs = Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion,
  "org.apache.spark" %% "spark-sql" % sparkVersion
)

// JAR build settings
lazy val commonSettings = Seq(
  organization := "dzlab",
  version := "0.1",
  scalaSource in Compile := baseDirectory.value / "src",
  scalaSource in Test := baseDirectory.value / "test",
  resourceDirectory in Test := baseDirectory.value / "test" / "resources",
  javacOptions ++= Seq(),
  scalacOptions ++= Seq(
    "-deprecation",
    "-feature",
    "-language:implicitConversions",
    "-language:postfixOps"
  ),
  libraryDependencies ++= sparkLibs
)

// Docker Image build settings
dockerBaseImage := "gcr.io/spark-operator/spark:v" + sparkVersion

val registry = "192.168.64.11:5000"

lazy val root = (project in file("."))
  .enablePlugins(
    DockerPlugin,
    JavaAppPackaging
  )
  .settings(
    name := "spark-k8s",
    commonSettings,
    dockerAliases ++= Seq(
      dockerAlias.value.withRegistryHost(Some(registry))
    ),
    mainClass in (Compile, run) := Some("dzlab.SparkJob")
  )
