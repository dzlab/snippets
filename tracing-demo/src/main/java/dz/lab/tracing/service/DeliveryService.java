package dz.lab.tracing.service;

import dz.lab.tracing.utils.*;
import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Scope;
import io.opentracing.Span;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DeliveryService {

    private final JaegerTracer tracer;

    public DeliveryService(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/arrangeDelivery")
    public void arrangeDelivery() {
        Span parentSpan = tracer.scopeManager().activeSpan();
        Span span = tracer.buildSpan("DeliveryService").start();
		Scope scope = tracer.scopeManager().activate(span);
        HttpUtils.doGet("http://localhost:8080/transport");
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}