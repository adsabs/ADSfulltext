import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
//import static org.junit.matchers.JUnitMatchers.*; // for hasItem()

import org.adslabs.adsfulltext.Worker;

public class WorkerTest {

    public Worker worker = new Worker();

    @Ignore("not yet ready") @Test
    public void testWorkerCanConnectToRabbitMQ() {

    }
}