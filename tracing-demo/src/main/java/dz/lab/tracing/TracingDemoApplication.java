package dz.lab.tracing;

import io.jaegertracing.Configuration;
import io.jaegertracing.Configuration.ReporterConfiguration;
import io.jaegertracing.Configuration.SamplerConfiguration;
import io.jaegertracing.Configuration.SenderConfiguration;
import io.jaegertracing.internal.JaegerTracer;
import io.jaegertracing.internal.samplers.ConstSampler;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class TracingDemoApplication {

	public static void main(String[] args) {
		SpringApplication.run(TracingDemoApplication.class, args);
	}

	@Bean
	public static JaegerTracer getTracer() {
        return Configuration.fromEnv("EShop").getTracer();
	}
}
