//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is to test the Worker class. This is a set of integration tests to ensure that the worker
// can do the following when interacting with RabbitMQ:
// 1. Connect to the queue
// 2. Consume from the queue
// 3. Publish to the queue
//
// All tests should be self explanatory along with the descriptive annotations

import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
//import static org.junit.matchers.JUnitMatchers.*; // for hasItem()

import com.rabbitmq.client.DefaultConsumer;
import com.rabbitmq.client.QueueingConsumer;

import org.adslabs.adsfulltext.Worker;
import org.adslabs.adsfulltext.TaskMaster;

import java.util.concurrent.TimeUnit;

public class WorkerTest {

    // Variable declaration
    // -------------------------------------
    public Worker worker = new Worker();
    public TaskMaster TM = new TaskMaster();
    // -------------------------------------

    // Junit init of master classes
    //
    @Before
    public void setUp() {

        // Make sure the queues exist
        this.TM.initialize_rabbitmq();

        // Connect the worker
        this.worker.connect();
    }

    @After
    public void tearDown() {

        // Disconnect the worker from the queue
        this.worker.disconnect();

        // Purge all queues / clean up
        this.TM.purge_queues();
    }

    // Helper methods
    //
    @Ignore("Helper method")
    public int helper_message_count(String queueName) {

        int queue_number = 100;
        try {
            queue_number = this.worker.channel.queueDeclarePassive(queueName).getMessageCount();
            return queue_number;
        } catch (java.io.IOException error) {
            System.out.println("IO Error: " + error.getMessage());
            return queue_number;
        }
    }

    // Old tests
    //
    @Ignore("Now a part of setUp and tearDown") @Test
    public void testWorkerCanConnectToRabbitMQ() {

        // Connect to RabbitMQ
        boolean result = this.worker.connect();
        assertEquals(true, result);
        boolean closed = this.worker.disconnect();
        assertEquals(true, closed);
    }

    // Full test suite
    //
    @Test
    public void testWorkerCanDeclareQueues() {

        // Declare all the queues
        boolean result = this.worker.declare_all();
        assertEquals(true, result);
    }

    @Test
    public void testWorkerCanPurgeQueues() {

        // Purge all the queues
        boolean result = this.worker.purge_all();
        assertEquals(true, result);

    }

    @Ignore("until the other test is complete") @Test
    public void testWorkerCanExtractcontentFromMessage() {

        // Define some constants
        // -----------------------------------
        String messageBody = "Test";
        String exchangeName = "FulltextExtractionExchange";
        String routeKey = "PDFFileExtractorRoute";
        String queueName = "PDFFileExtractorQueue";
        String expectedBody = "Test Processed";
        boolean autoAck = false;
        // -----------------------------------

        // Publish to the queue the fake message
        //
        boolean result = this.TM.publish(exchangeName, routeKey, messageBody);
        assertEquals(true, result);
        assertEquals(1, helper_message_count(queueName));

        // Consume from the queue
        //
        this.worker.run();

        // Check the queue has a message
        //
        assertEquals(1, helper_message_count("WriteMetaFileQueue"));

        // Obtain the message and check it was processed as expected
        //

//        -------------------------------------------------------
//        Ignore this part until the PDFExtractor is implemented
//        -------------------------------------------------------
//        try {
//            // We want to check that the message that got sent to the next queue
//            // is the message we expected
//            QueueingConsumer consumer = new QueueingConsumer(this.worker.channel);
//            this.worker.channel.basicConsume("WriteMetaFileQueue", false, consumer);
//            QueueingConsumer.Delivery delivery = consumer.nextDelivery();
//            String message = new String(delivery.getBody());
//            long deliveryTag = delivery.getEnvelope().getDeliveryTag();
//            this.worker.channel.basicAck(deliveryTag, false);
//
//            // Check with expected
//            assertEquals(expectedBody, message);
//
//        } catch (java.io.IOException error) {
//            System.out.println("IOError");
//            assertEquals(1, 0);
//        } catch (java.lang.InterruptedException error) {
//            System.out.println("IOError");
//            assertEquals(1,0);
//        }
//        // Check the queue is empty
//        //
//        assertEquals(0, helper_message_count("WriteMetaFileQueue"));
    }

}