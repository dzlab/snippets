package dz.lab.tracing;

import io.jaegertracing.internal.JaegerTracer;
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
		String response = "You have successfully checked out your shopping cart.";
		span.setTag("http.status_code", 200);
		span.finish();
		return response;
	}

}