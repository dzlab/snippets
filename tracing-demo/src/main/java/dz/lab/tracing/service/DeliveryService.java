package dz.lab.tracing.service;

import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Span;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.stereotype.Service;

@Service("ds")
public class DeliveryService {

    private final JaegerTracer tracer;
	private final LogisticsService logisticsService;

    public DeliveryService(JaegerTracer tracer, LogisticsService logisticsService) {
        this.tracer = tracer;
        this.logisticsService = logisticsService;
    }

    public void arrangeDelivery(Span parentSpan) {
        Span span = tracer.buildSpan("DeliveryService").asChildOf(parentSpan).start();
        logisticsService.transport(span);
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}