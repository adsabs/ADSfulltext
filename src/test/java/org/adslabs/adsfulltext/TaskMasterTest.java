//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is to test the TaskMaster class. This it to ensure that the TaskMaster can correctly
// initialise the RabbitMQ system - i.e., to check that the correct queues exist. It also has some
// other helper functions for general maintenance of RabbitMQ.
//
// All tests should be self explanatory

import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;

import org.adslabs.adsfulltext.TaskMaster;

public class TaskMasterTest {

    // Variable declaration
    // -------------------------------------
    public TaskMaster TM = new TaskMaster();
    // -------------------------------------

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