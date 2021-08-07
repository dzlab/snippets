package dz.lab.tracing;

import dz.lab.tracing.utils.*;
import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Scope;
import io.opentracing.Span;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
public class EShopController {

    Logger logger = LoggerFactory.getLogger(this.getClass());
    private final JaegerTracer tracer;

    public EShopController(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/checkout")
	public String checkout(@RequestHeader HttpHeaders headers) {
		String user = headers.get(HttpHeaders.USER_AGENT).get(0);
        logger.info("User is: '" + user + "'.");
		Span span = tracer.buildSpan("checkout").start();
		// set the created span as the active span for the current context(thread) using ScopeManager.active method before calling subsequent functions.
		Scope scope = tracer.scopeManager().activate(span);
		span.setBaggageItem(HttpHeaders.USER_AGENT, user);
		HttpClient client = new HttpClient(tracer, span);
		client.doGet("http://inventory:8080/createOrder");
		client.doGet("http://billing:8080/payment");
		client.doGet("http://delivery:8080/arrangeDelivery");
		String response = "You have successfully checked out your shopping cart.";
		span.setTag("http.status_code", 200);
		span.finish();
		return response;
	}

}