package dz.lab.tracing.utils;

import io.opentracing.propagation.TextMap;
import org.springframework.http.HttpHeaders;

import java.util.Iterator;
import java.util.Map;

/**
 * @see https://github.com/opentracing-contrib/java-spring-web/blob/master/opentracing-spring-web/src/main/java/io/opentracing/contrib/spring/web/client/HttpHeadersCarrier.java
 */
public class HttpHeadersCarrier implements TextMap {

    private HttpHeaders httpHeaders;

    public HttpHeadersCarrier(HttpHeaders httpHeaders)  {
        this.httpHeaders = httpHeaders;
    }

    @Override
    public void put(String key, String value) {
        httpHeaders.add(key, value);
    }

    @Override
    public Iterator<Map.Entry<String, String>> iterator() {
        return this.httpHeaders.toSingleValueMap().entrySet().iterator();
    }
}