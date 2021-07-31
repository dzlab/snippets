package dz.lab.tracing;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EShopController {

	@GetMapping("/checkout")
	public String checkout() {
		return "You have successfully checked out your shopping cart.";
	}

}