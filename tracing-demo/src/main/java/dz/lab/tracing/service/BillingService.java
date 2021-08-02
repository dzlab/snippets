package dz.lab.tracing.service;

import dz.lab.tracing.utils.*;
import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.propagation.Format;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;

@RestController
public class BillingService {

    private final JaegerTracer tracer;

    public BillingService(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/payment")
    public void payment(@RequestHeader HttpHeaders headers) {
        SpanContext parent = tracer.extract(Format.Builtin.HTTP_HEADERS, new HttpHeadersCarrier(headers));
        Span span = tracer.buildSpan("payment").asChildOf(parent).start();
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}