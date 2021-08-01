package dz.lab.tracing.service;

import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Span;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
class LogisticsService {

    private final JaegerTracer tracer;

    public LogisticsService(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/transport")
    public void transport() {
        Span span = tracer.buildSpan("LogisticsService").start();
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}