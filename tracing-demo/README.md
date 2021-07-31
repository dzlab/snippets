# tracing demo

Useful commands to build/run the application
```
$ export JAVA_HOME=`/usr/libexec/java_home -v 14`
$ /mvnw package
$ /mvnw spring-boot:run
$ docker build -t dzlab/tracing-demo .
$ docker run -p 8080:8080 dzlab/tracing-demo
```