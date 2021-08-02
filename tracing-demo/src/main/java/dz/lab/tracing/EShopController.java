package dz.lab.tracing;

import dz.lab.tracing.utils.*;
import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Scope;
import io.opentracing.Span;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EShopController {

    private final JaegerTracer tracer;

    public EShopController(JaegerTracer tracer) {
        this.tracer = tracer;
    }

	@GetMapping("/checkout")
	public String checkout() {
		Span span = tracer.buildSpan("checkout").start();
		// set the created span as the active span for the current context(thread) using ScopeManager.active method before calling subsequent functions.
		Scope scope = tracer.scopeManager().activate(span);
		HttpClient client = new HttpClient(tracer, span);
		client.doGet("http://localhost:8080/createOrder");
		client.doGet("http://localhost:8080/payment");
		client.doGet("http://localhost:8080/arrangeDelivery");
		String response = "You have successfully checked out your shopping cart.";
		span.setTag("http.status_code", 200);
		span.finish();
		return response;
	}

}