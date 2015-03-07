import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
//import static org.junit.matchers.JUnitMatchers.*; // for hasItem()

import org.adslabs.adsfulltext.Worker;
import org.adslabs.adsfulltext.TaskMaster;

public class WorkerTest {

    public Worker worker = new Worker();

    @Before
    public void setUp() {
        this.worker.connect();
    }

    @After
    public void tearDown() {
        this.worker.disconnect();
    }

    @Ignore("Now a part of setUp and tearDown") @Test
    public void testWorkerCanConnectToRabbitMQ() {

        // Connect to RabbitMQ
        boolean result = this.worker.connect();
        assertEquals(true, result);
        boolean closed = this.worker.disconnect();
        assertEquals(true, closed);
    }

    @Test
    public void testWorkerCanDeclareQueues() {

        // Declare all the queues
        boolean result = this.worker.declare_all();
        assertEquals(true, result);

    }

    @Test
    public void testWorkerCanPurgeQueues() {

        boolean result = this.worker.purge_all();
        assertEquals(true, result);

    }

    @Test
    public void testWorkerCanSubscribetoAPDFQueue() {

        // Make sure the queues exist
        TaskMaster TM = new TaskMaster();
        TM.initialize_rabbitmq();

        // Publish message to the queue
        String messageBody = "Test";
        String exchangeName = "FulltextExtractionExchange";
        String routeKey = "PDFFileExtractorRoute";
        boolean result = TM.publish(exchangeName, routeKey, messageBody);

        // Consume from the queue
        String messageReturn = this.worker.subscribe();

        assertEquals(messageBody, messageReturn);

        // Clean up
        TM.purge_queues();
    }

    @Test
    public void testWorkerCanExtractcontentFromMessage() {

        // Make sure the queues exist
        TaskMaster TM = new TaskMaster();
        TM.initialize_rabbitmq();

        // Publish message to the queue
        String messageBody = "Test";
        String exchangeName = "FulltextExtractionExchange";
        String routeKey = "PDFFileExtractorRoute";
        String queueName = "PDFFileExtractorQueue";
        boolean result = TM.publish(exchangeName, routeKey, messageBody);

        int queue_number;
        try {
            queue_number = this.worker.channel.queueDeclarePassive(queueName).getMessageCount();
            assertEquals(1, queue_number);
        } catch (java.io.IOException error) {
            System.out.println("IO Error: " + error.getMessage());
        }

        // Consume from the queue
        this.worker.run();

        // Check the queue is empty
        try {
            queue_number = this.worker.channel.queueDeclarePassive(queueName).getMessageCount();
            assertEquals(0, queue_number);
        } catch (java.io.IOException error) {
            System.out.println("IO Error: " + error.getMessage());
        }

        // Clean up
        TM.purge_queues();

    }

}