package dz.lab.tracing.service;

import dz.lab.tracing.utils.*;
import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Scope;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.propagation.Format;
import io.opentracing.tag.Tags;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
public class BillingService {

    Logger logger = LoggerFactory.getLogger(this.getClass());
    private final JaegerTracer tracer;

    public BillingService(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/payment")
    public void payment(@RequestHeader HttpHeaders headers) {
        // SpanContext parent = tracer.extract(Format.Builtin.HTTP_HEADERS, new HttpHeadersCarrier(headers));
        // Span span = tracer.buildSpan("payment").asChildOf(parent)
        //     .withTag(Tags.SPAN_KIND.getKey(), Tags.SPAN_KIND_SERVER)
        //     .start();
        // Scope scope = tracer.scopeManager().activate(span);
        // String user = span.getBaggageItem(HttpHeaders.USER_AGENT);
        // logger.info("User is: '" + user + "'.");
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 1000));
        } catch (InterruptedException e) {}
        // span.finish();
    }
}