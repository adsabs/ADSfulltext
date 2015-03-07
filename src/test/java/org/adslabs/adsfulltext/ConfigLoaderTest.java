import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
//import static org.junit.matchers.JUnitMatchers.*; // for hasItem()

import org.adslabs.adsfulltext.ConfigLoader;

public class ConfigLoaderTest {

    public ConfigLoader config = new ConfigLoader();

    @Test
    public void testCanExtractCorrectContentFromConfig() {
        config.loadConfig();
        assertThat(config.data.RABBITMQ_URI, containsString("amqp"));
        assertEquals(config.data.ERROR_HANDLER.exchange, "FulltextExtractionExchange");
    }

    @Test
    public void testCanExtractArrayfromYAML() {
        config.loadConfig();
        assertTrue(config.data.EXCHANGES.length > 0);
        System.out.println("Array content: " + config.data.EXCHANGES[0].exchange);
        assertThat(config.data.EXCHANGES[0].exchange, containsString("Exchange"));
        assertThat(config.data.QUEUES[0].queue, containsString("Queue"));
    }
}
