import static org.junit.Assert.*;
import org.junit.Test;

import org.adslabs.adsfulltext.ConfigLoader;

public class ConfigLoaderTest {

    public ConfigLoader config = new ConfigLoader();

    @Test
    public void testConfigIsLoadedCorrectly() {
        config.loadYAML();
        assertEquals(config.getName(), "FULLTEXT_EXTRACT_PATH");
    }

}
