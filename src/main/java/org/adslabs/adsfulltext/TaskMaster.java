//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is meant to reflect the same class that exists in the Python library. However, the functionality
// is only intended to be a helper function for the integration tests of the worker function. This is simply,
// to do things such as:
// 1. Purge all the queues
// 2. Publish messages to a queue
// 3. Generate all of the queues
//
package org.adslabs.adsfulltext;

import org.adslabs.adsfulltext.ConfigLoader;
import org.adslabs.adsfulltext.Worker;

public class TaskMaster {

    public Worker w;
    public ConfigLoader config;

    public TaskMaster() {
        config = new ConfigLoader();
        config.loadConfig();
    }

    // Initialise all of the queues from the settings.yaml file
    //
    public boolean initialize_rabbitmq() {

        w = new Worker();
        w.connect();
        w.declare_all();
        w.disconnect();

        return true;
    }

    // Publish a message to the queue specified
    //
    public boolean publish(String exchangeName, String routingKey, String messageBody) {

        try {
            w = new Worker();
            w.connect();
            w.channel.basicPublish(exchangeName, routingKey, null, messageBody.getBytes());
            w.disconnect();
            return true;
        } catch (java.io.IOException error){
            System.out.println("IOError, is rabbitMQ on? Does the exchange exist?" + error.getMessage());
            return false;
        }
    }

    // Purge all the queues from the settings.yaml file
    //
    public boolean purge_queues() {

        w = new Worker();
        w.connect();
        boolean result = w.purge_all();
        w.disconnect();
        return true;
    }
}
