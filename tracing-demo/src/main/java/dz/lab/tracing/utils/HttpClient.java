package dz.lab.tracing.utils;

import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Span;
import io.opentracing.propagation.Format;
import io.opentracing.propagation.TextMap;
import io.opentracing.propagation.TextMapExtractAdapter;
import io.opentracing.tag.Tags;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

public class HttpClient {

    private final JaegerTracer tracer;
    private final Span span;

    public HttpClient(JaegerTracer tracer, Span span) {
        this.tracer = tracer;
        this.span = span;
    }

    public String doGet(String url) {
        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        TextMap httpHeadersCarrier = new HttpHeadersCarrier(headers);
        Tags.SPAN_KIND.set(tracer.activeSpan(), Tags.SPAN_KIND_CLIENT);
        Tags.HTTP_METHOD.set(tracer.activeSpan(), "GET");
        Tags.HTTP_URL.set(tracer.activeSpan(), url.toString());
        tracer.inject(span.context(), Format.Builtin.HTTP_HEADERS, httpHeadersCarrier);
        HttpEntity<String> entity = new HttpEntity<>("body", headers);
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);
        return response.getBody();
    }

}