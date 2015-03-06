package org.adslabs.adsfulltext;

import org.adslabs.adsfulltext.ConfigLoader;
import org.adslabs.adsfulltext.Worker;

public class TaskManager {

    public Worker w;
    public ConfigLoader config;

    public TaskManager() {
        config = new ConfigLoader();
        config.loadConfig();
    }

    public boolean initialize_rabbitmq() {

        w = new Worker();
        w.connect();

        return true;
    }

}
