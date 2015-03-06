import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;

import org.adslabs.adsfulltext.TaskManager;

public class TaskManagerTest {

    public TaskManager TM = new TaskManager();

    @Ignore("Complete other tests first") @Test
    public void testConnectingToQueue() {

        // Initialize the rabbit system
        boolean result = TM.initialize_rabbitmq();
        assertEquals(result, true);

    }
}