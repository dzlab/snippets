# Distributed Tracing with Jaeger

Useful commands to build/run the application
```
$ export JAVA_HOME=`/usr/libexec/java_home -v 14`
$ ./mvnw package
$ ./mvnw spring-boot:run
```

Build and run the application
```
$ docker build -t dzlab/tracing-demo .
$ docker run -p 8080:8080 dzlab/tracing-demo
```

Visit http://localhost:8080/checkout

Start jaeger all in one Docker image - [link](https://www.jaegertracing.io/docs/1.6/getting-started/)
```
$ docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 9411:9411 \
  jaegertracing/all-in-one:1.6
```

Navigate to http://localhost:16686 to access the Jaeger UI.

Resources:
- 
- A minimalistic guide to distributed tracing with OpenTracing and Jaeger - [link](https://shekhargulati.com/2019/04/08/a-minimalistic-guide-to-distributed-tracing-with-opentracing-and-jaeger/)