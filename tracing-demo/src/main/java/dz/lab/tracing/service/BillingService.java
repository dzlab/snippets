package dz.lab.tracing.service;

import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Span;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class BillingService {

    private final JaegerTracer tracer;

    public BillingService(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/payment")
    public void payment() {
        // Current active span will be the parent of the newly created span
        Span span = tracer.buildSpan("BillingService").start();
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}