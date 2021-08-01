package dz.lab.tracing.service;

import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Span;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InventoryService {

    private final JaegerTracer tracer;

    public InventoryService(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/createOrder")
    public void createOrder() {
        Span span = tracer.buildSpan("InventoryService").start();
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}