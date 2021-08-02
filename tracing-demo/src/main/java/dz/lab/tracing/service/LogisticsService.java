package dz.lab.tracing.service;

import dz.lab.tracing.utils.*;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.Tracer;
import io.opentracing.propagation.Format;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;

@RestController
class LogisticsService {

    private final Tracer tracer;

    public LogisticsService(Tracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/transport")
    public void transport(@RequestHeader HttpHeaders headers) {
        SpanContext parent = tracer.extract(Format.Builtin.HTTP_HEADERS, new HttpHeadersCarrier(headers));
        Span span = tracer.buildSpan("transport").asChildOf(parent).start();
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        span.finish();
    }
}