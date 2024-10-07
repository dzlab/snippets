name := "employees"
version := "0.1.0"
scalaVersion := "2.12.19"

libraryDependencies ++= Seq(
    "org.apache.calcite" % "calcite-core" % "1.37.0",
    "org.scalatest" %% "scalatest" % "3.2.15" % Test
)
libraryDependencies ++= Seq(
    "com.fasterxml.jackson.core" % "jackson-databind" % "2.17.0",
    "com.fasterxml.jackson.module" %% "jackson-module-scala" % "2.17.2"
)