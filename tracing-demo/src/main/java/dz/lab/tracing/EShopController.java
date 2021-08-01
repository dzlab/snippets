package dz.lab.tracing;

import dz.lab.tracing.service.*;
import io.jaegertracing.internal.JaegerTracer;
import io.opentracing.Scope;
import io.opentracing.Span;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EShopController {

    private final JaegerTracer tracer;

	private final BillingService billingService;
	private final DeliveryService deliveryService;
	private final InventoryService inventoryService;

    public EShopController(
		JaegerTracer tracer,
		BillingService billingService,
		DeliveryService deliveryService,
		InventoryService inventoryService
		) {
        this.tracer = tracer;
        this.billingService = billingService;
        this.deliveryService = deliveryService;
        this.inventoryService = inventoryService;
    }

	@GetMapping("/checkout")
	public String checkout() {
		Span span = tracer.buildSpan("checkout").start();
		// set the created span as the active span for the current context(thread) using ScopeManager.active method before calling subsequent functions.
		Scope scope = tracer.scopeManager().activate(span);
		inventoryService.createOrder();
		billingService.payment();
		deliveryService.arrangeDelivery();
		String response = "You have successfully checked out your shopping cart.";
		span.setTag("http.status_code", 200);
		span.finish();
		return response;
	}

}