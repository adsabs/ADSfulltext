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

    public boolean initialize_rabbitmq() {

        w = new Worker();
        w.connect();
        w.declare_all();
        w.disconnect();

        return true;
    }

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

    public boolean purge_queues() {

        w = new Worker();
        w.connect();
        boolean result = w.purge_all();
        w.disconnect();
        return true;
    }
}
