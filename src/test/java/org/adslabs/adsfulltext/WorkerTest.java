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

import org.json.JSONObject;
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

import java.util.Map;
import java.util.concurrent.TimeUnit;

public class WorkerTest {

    // Variable declaration
    // -------------------------------------
    public Worker worker = new Worker();
    public TaskMaster TM = new TaskMaster();

    // JSON payload, typical payload should be received as a byte:
    // {
    // "bibcode": "test",
    // "file_format": "pdf",
    // "UPDATE": "NOT_EXTRACTED_BEFORE",
    // "meta_path": "some_path.json",
    // "index_date": "2015-03-02T19:12:57.387093Z",
    // "provider": "Elsevier",
    // "ft_source": "/vagrant/src/test/resources/test_doc.pdf";
    // }
    String pdf_path = getClass().getResource("/test_doc.pdf").getFile();
    String testMessageJSON = "[{\"bibcode\": \"test\", \"file_format\": \"pdf\", \"UPDATE\": \"NOT_EXTRACTED_BEFORE\", \"meta_path\": \"some_path.json\", \"index_date\": \"2015-03-02T19:12:57.387093Z\", \"provider\": \"Elsevier\", \"ft_source\": \"" + pdf_path + "\"}]";
    String testMessageJSONNonExistentFile = "[{\"bibcode\": \"test\", \"file_format\": \"pdf\", \"UPDATE\": \"NOT_EXTRACTED_BEFORE\", \"meta_path\": \"some_path.json\", \"index_date\": \"2015-03-02T19:12:57.387093Z\", \"provider\": \"Elsevier\", \"ft_source\": \"/vagrant/src/test/resources/test_non_existent.pdf\"}]";

    // Queues
    String exchangeName = "FulltextExtractionExchange";
    String routeKey = "PDFFileExtractorRoute";
    String queueName = "PDFFileExtractorQueue";
    String expectedBody = "This is a PDF document";
    String WriteMetaFileQueue = "WriteMetaFileQueue";
    String ErrorQueue = "ErrorHandlerQueue";
    String PDFClassName = "org.adslabs.adsfulltext.PDFExtractList";
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

    @Test
    public void testWorkerCanExtractcontentFromMessage() throws Exception {

        // Publish to the queue the fake message
        //
        boolean result = this.TM.publish(this.exchangeName, this.routeKey, this.testMessageJSON);
        assertEquals(true, result);
        assertEquals(1, helper_message_count(this.queueName));

        // Consume from the queue
        //
        this.worker.run();

        // Check the queue has a message
        //
        assertEquals(1, helper_message_count(WriteMetaFileQueue));

        // Obtain the message and check it was processed as expected
        //
        // We want to check that the message that got sent to the next queue
        // is the message we expected
        QueueingConsumer consumer = new QueueingConsumer(this.worker.channel);
        this.worker.channel.basicConsume(this.WriteMetaFileQueue, false, consumer);
        QueueingConsumer.Delivery delivery = consumer.nextDelivery();
        String message = new String(delivery.getBody());
        long deliveryTag = delivery.getEnvelope().getDeliveryTag();
        this.worker.channel.basicAck(deliveryTag, false);

        // Check with expected
        assertThat(message, containsString(this.expectedBody));

        // Check the queue is empty
        //
        assertEquals(0, helper_message_count(this.WriteMetaFileQueue));
    }

    @Test
    public void testWorkerPublishesToErrorHandlerIfProblem() throws Exception {

        // Publish to the queue the fake message
        //
        boolean result = this.TM.publish(this.exchangeName, this.routeKey, this.testMessageJSONNonExistentFile);
        assertEquals(true, result);
        assertEquals(1, helper_message_count(this.queueName));

        // Consume from the queue
        //
        this.worker.run();

        // Check the queue has a message
        //
        assertEquals(0, helper_message_count(this.WriteMetaFileQueue));
        assertEquals(1, helper_message_count(this.ErrorQueue));

        // We want to check that the message that got sent to the next queue
        // is the message we expected
        QueueingConsumer consumer = new QueueingConsumer(this.worker.channel);
        this.worker.channel.basicConsume(this.ErrorQueue, false, consumer);
        QueueingConsumer.Delivery delivery = consumer.nextDelivery();

        String message = new String(delivery.getBody());
        JSONObject payload = new JSONObject(message);

        long deliveryTag = delivery.getEnvelope().getDeliveryTag();
        this.worker.channel.basicAck(deliveryTag, false);

        // Check with expected
        assertTrue(payload.has(PDFClassName));
    }

}