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
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class HttpClient {
    private static Logger logger = LoggerFactory.getLogger("HttpClient");

    private final JaegerTracer tracer;
    private final Span span;

    public HttpClient(JaegerTracer tracer, Span span) {
        this.tracer = tracer;
        this.span = span;
    }

    public String doGet(String url) {
        return this.doGet(url, new HttpHeaders());
    }

    public String doGet(String url, HttpHeaders headers) {
        RestTemplate restTemplate = new RestTemplate();
        // TextMap httpHeadersCarrier = new HttpHeadersCarrier(headers);
        // Tags.SPAN_KIND.set(tracer.activeSpan(), Tags.SPAN_KIND_CLIENT);
        // Tags.HTTP_METHOD.set(tracer.activeSpan(), "GET");
        // Tags.HTTP_URL.set(tracer.activeSpan(), url.toString());
        // tracer.inject(span.context(), Format.Builtin.HTTP_HEADERS, httpHeadersCarrier);
        HttpEntity<String> entity = new HttpEntity<>("", headers);
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);
        return response.getBody();
    }

    public static HttpHeaders copyIstioHeaders(HttpHeaders inHeaders) {
        Map<String, String> inHeadersMap = inHeaders.toSingleValueMap();
        HttpHeaders outHeaders = new HttpHeaders();

		String requestId = inHeadersMap.get("x-request-id");
		outHeaders.add("x-request-id", requestId);
        logger.info("x-request-id: '" + requestId + "'.");

		String b3TraceId = inHeadersMap.get("x-b3-traceid");
		outHeaders.add("x-b3-traceid", b3TraceId);
        logger.info("x-b3-traceid: '" + b3TraceId + "'.");

		String b3SpanId = inHeadersMap.get("x-b3-spanid");
		outHeaders.add("x-b3-spanid", b3SpanId);
        logger.info("x-b3-spanid: '" + b3SpanId + "'.");

		String b3ParentSpanId = inHeadersMap.get("x-b3-parentspanid");
		outHeaders.add("x-b3-parentspanid", b3ParentSpanId);
        logger.info("x-b3-parentspanid: '" + b3ParentSpanId + "'.");

		String b3Sampled = inHeadersMap.get("x-b3-sampled");
		outHeaders.add("x-b3-sampled", b3Sampled);
        logger.info("x-b3-sampled: '" + b3Sampled + "'.");

		String b3Flags = inHeadersMap.get("x-b3-flags");
		outHeaders.add("x-b3-flags", b3Flags);
        logger.info("x-b3-flags: '" + b3Flags + "'.");

		String spanContext = inHeadersMap.get("x-ot-span-context");
		outHeaders.add("x-ot-span-context", spanContext);
        logger.info("x-ot-span-context: '" + spanContext + "'.");

		return outHeaders;
	}


}