import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
//import static org.junit.matchers.JUnitMatchers.*; // for hasItem()

import org.adslabs.adsfulltext.ConfigLoader;

public class ConfigLoaderTest {

    public ConfigLoader config = new ConfigLoader();

    @Test
    public void testCanExtracCorrectContentFromConfig() {
        config.loadConfig();
        assertThat(config.data.RABBITMQ_URL, containsString("amqp"));
        assertEquals(config.data.ERROR_HANDLER.exchange, "FulltextExtractionExchange");
    }
}
