package org.adslabs.adsfulltext;

import org.adslabs.adsfulltext.ErrorQueue;
import org.adslabs.adsfulltext.Exchanges;
import org.adslabs.adsfulltext.Queues;

import java.util.List;

public class YamlConfig {

    public String RABBITMQ_URI;
    public ErrorQueue ERROR_HANDLER;
    public Exchanges[] EXCHANGES;
    public Queues[] QUEUES;
}