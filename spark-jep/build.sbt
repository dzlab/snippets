
name := "spark-python"
version := "1.0"
scalaVersion := "2.12.0"

val sparkVersion = "3.1.2"

val sparkLibs = Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion,
  "org.apache.spark" %% "spark-sql" % sparkVersion
)

val pythonLibs = Seq(
  "black.ninia" % "jep" % "3.9.1"
)

libraryDependencies ++= sparkLibs ++ pythonLibs

mainClass in (Compile, run) := Some("dzlab")

def nativeLibraryPath = s"${sys.env.get("JAVA_LIBRARY_PATH") orElse sys.env.get("LD_LIBRARY_PATH") orElse sys.env.get("DYLD_LIBRARY_PATH") getOrElse "."}:."

javaOptions in Test += s"-Djava.library.path=$nativeLibraryPath"
javaOptions in runMain += s"-Djava.library.path=$nativeLibraryPath"