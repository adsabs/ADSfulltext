import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;

import org.adslabs.adsfulltext.TaskMaster;

public class TaskMasterTest {

    public TaskMaster TM = new TaskMaster();

    @Test
    public void testConnectingToQueue() {

        // Initialise the rabbit system
        boolean result = TM.initialize_rabbitmq();
        assertEquals(result, true);
    }

    @Test
    public void testCanPublishToAndPurgeQueuesOfTheirContent() {

        // Initialise the rabbit system
        TM.initialize_rabbitmq();

        // Publish message to the queue
        String messageBody = "test";
        String exchangeName = "FulltextExtractionExchange";
        String routeKey = "PDFFileExtractorRoute";
        boolean result_publish = TM.publish(exchangeName, routeKey, messageBody);
        assertEquals(true, result_publish);

        boolean result_purge = TM.purge_queues();
        assertEquals(true, result_purge);
    }


}