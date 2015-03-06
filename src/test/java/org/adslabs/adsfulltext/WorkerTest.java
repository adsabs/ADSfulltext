import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
//import static org.junit.matchers.JUnitMatchers.*; // for hasItem()

import org.adslabs.adsfulltext.Worker;
import org.adslabs.adsfulltext.TaskManager;

public class WorkerTest {

    public Worker worker = new Worker();

    @Test
    public void testWorkerCanConnectToRabbitMQ() {

        // Connect to RabbitMQ
        boolean result = this.worker.connect();
        assertEquals(result, true);
        boolean closed = this.worker.disconnect();
        assertEquals(closed, true);
    }

    @Test
    public void testWorkerCanDeclareQueues() {

        // Connect to the queue
        this.worker.connect();

        // Declare all the queues
        boolean result = this.worker.declare_all();

        assertEquals(result, true);

    }

    @Test
    public void testWorkerCanSubscribetoAPDFQueue() {

        // Connect to the queue
        this.worker.connect();

        // Publish a fake message to the queue
        TaskManagerTest TM = new TaskManagerTest();

        // Consume from the queue
        String message = this.worker.subscribe();

        assertEquals(message, "Test");

        this.worker.disconnect();

    }
}