//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class contains the functionality of the PDF Extractor Worker that includes:
// 1. Connecting to queues
// 2. Consuming from the queues
// 3. Reducing/Parsing the correct content
// 4. Publishing to the next queue
//
// The idea is that the number of workers will be controlled by supervisord, as it will remove the need
// to manage two different daemon systems - given that supervisord already controls the Python system.
//

package org.adslabs.adsfulltext;

import com.rabbitmq.client.Connection;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.DefaultConsumer;
import com.rabbitmq.client.QueueingConsumer;
import com.rabbitmq.client.Envelope;
import com.rabbitmq.client.AMQP;

import org.adslabs.adsfulltext.ConfigLoader;

import java.util.HashMap;
import java.util.Map;

import org.json.JSONObject;
import org.json.JSONArray;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.adslabs.adsfulltext.Exchanges;
import org.adslabs.adsfulltext.Queues;
import org.adslabs.adsfulltext.PDFExtractList;

public class Worker {

    // Variable declaration
    // --------------------------
    public Connection connection;
    public Channel channel;
    int prefetchCount;
    ConfigLoader config;
    boolean testRun;
    static Logger logger = LoggerFactory.getLogger(Worker.class);
    // --------------------------

    // Class constructor
    //
    public Worker() {
        prefetchCount = 1;
        config = new ConfigLoader();
        config.loadConfig();
        this.testRun = true;
    }

    // Constructor overload with option of testRun
    public Worker(boolean _testRun) {
        prefetchCount = 1;
        config = new ConfigLoader();
        config.loadConfig();
        this.testRun = _testRun;
    }

    public boolean disconnect() {
        try {
            logger.info("Cleaning up connections.");
            this.channel.close();
            this.connection.close();
            return true;

        } catch (java.io.IOException error) {

            logger.error("There is probably no connection with RabbitMQ currently made: ", error.getMessage());
            return false;

        }
    }

    public boolean connect () {

        ConnectionFactory rabbitMQInstance;

        // This creates a connection object, that allows connections to be open to the same
        // RabbitMQ instance running
        //
        // There seems to be a lot of catches, but each one should list the reason for it's raise
        //
        // It is not necessary to disconnect the connection, it should be dropped when the program exits
        // See the API guide for more info: https://www.rabbitmq.com/api-guide.html

        try {

            rabbitMQInstance = new ConnectionFactory();
            logger.info("Connecting to RabbitMQ instance: {}", this.config.data.RABBITMQ_URI);
            rabbitMQInstance.setUri(this.config.data.RABBITMQ_URI);
            this.connection = rabbitMQInstance.newConnection();
            this.channel = this.connection.createChannel();

            // This tells RabbitMQ not to give more than one message to a worker at a time.
            // Or, in other words, don't dispatch a new message to a worker until it has processed
            // and acknowledged the previous one.
            this.channel.basicQos(this.prefetchCount);

            return true;

        } catch (java.net.URISyntaxException error) {

            logger.error("URI error: {}", error.getMessage());
            return false;

        } catch (java.io.IOException error) {

            logger.error("IO Error, is RabbitMQ running???: {}", error.getMessage());
            return false;

        } catch (java.security.NoSuchAlgorithmException error) {

            logger.error("Most likely an SSL related error: ", error.getMessage());
            return false;

        } catch (java.security.KeyManagementException error) {

            logger.error("Most likely an SSL related error: ", error.getMessage());
            return false;

        }
    }

    // The function to be used on the message obtained from the queue. Currently it doesn't
    // do anything meaningful, and should be replaced by Grobid or PDFBox functions.
    //
    public String process(String message) throws Exception {
        logger.info("Processing the PDF full text.");
        PDFExtractList PDFExtractorWorker = new PDFExtractList();
        String newMessage = PDFExtractorWorker.f(message);
        return newMessage;
    }

    // Connect to the specified queue and start consuming messages. This will break from the
    // consuming if the user passes information that this is actually for a test.
    //
    public void subscribe() {

        // for array in subscribe array:
        //   start basic_consume
        //   if this is not a testing phase, then stay consuming

        // --------------------------------------------------------
        // Variable declaration
        // --------------------------------------------------------
        String queueName = "PDFFileExtractorQueue";
        boolean autoAck = false; // This means it has to acknowledged manually
        String exchangeName = "FulltextExtractionExchange";
        String routingKey = "WriteMetaFileRoute";
        String errorHandler = "ErrorHandlerRoute";
        String PDFClassName = "org.adslabs.adsfulltext.PDFExtractList";

        logger.info("Subscribing to the queue: {}", queueName);
        QueueingConsumer consumer = new QueueingConsumer(this.channel);

        try {
            this.channel.basicConsume(queueName, autoAck, consumer);
        } catch (java.io.IOException error) {
            logger.error("IO Error, does the queue exist and is RabbitMQ running?: {}", error.getMessage());
        }

        while (true) {
            try {
                QueueingConsumer.Delivery delivery = consumer.nextDelivery();
                String message = new String(delivery.getBody());
                long deliveryTag = delivery.getEnvelope().getDeliveryTag();
                AMQP.BasicProperties properties = delivery.getProperties();

                // Process the message
                try {

                    // Process and publish to the next queue
                    String newMessage = this.process(message);
                    logger.info("Processing successful, publishing to: {}", routingKey);
                    this.channel.basicPublish(exchangeName, routingKey, properties, newMessage.getBytes());

                } catch (Exception error) {

                    // Publish to the error handler
                    logger.error("Failed to process, publishing {} to: {}", message, errorHandler);
                    JSONObject ErrorMessage = new JSONObject();
                    JSONArray payload = new JSONArray(message);
                    ErrorMessage.put(PDFClassName, payload);

//                    AMQP.BasicProperties.Builder builder = new AMQP.BasicProperties().builder();
//                    Map<String,Object> headerMap = new HashMap<String, Object>();
//                    headerMap.put("PACKET_FROM", "JAVA_PDF_QUEUE");
//                    builder.headers(headerMap);

                    this.channel.basicPublish(exchangeName, errorHandler, properties, ErrorMessage.toString().getBytes());

                } finally {
                    logger.info("Acknowledging message");
                    logger.info("TestRun: {}", this.testRun);
                    // Acknowledge the receipt of the message for either situation
                    this.channel.basicAck(deliveryTag, false);
                }

                // If it's a test, we don't want to sit here forever
                //
                if (this.testRun){
                    logger.info("Test has been defined, breaking out of consume.");
                    break;
                }

            } catch (java.io.IOException error) {
                logger.error("IO Error, does the queue exist and is RabbitMQ running?: {}", error.getMessage());
            } catch(java.lang.InterruptedException error) {
                logger.error("IO Error, does the queue exist and is RabbitMQ running?: {}", error.getMessage());
            }
        }
    }

    // Declares all the relevant queues needed on RabbitMQ
    //
    public boolean declare_all() {

        Exchanges[] exchange = config.data.EXCHANGES;

        for (int i = 0; i < exchange.length; i++) {
            try {
                // OUTDATED
                // Parameters are exchange name, type, passive, durable, autoDelete, arguments
                // OUTDATED
                // On github of the client api: exchange name, type, durable, autoDelete, internal
                // internal: internal true if the exchange is internal, i.e. can't be directly published to by a client.
                logger.info("Declaring the following queue; exchange: {}, type: {}, durable: {}, auto-delete: {}", exchange[i].exchange, exchange[i].exchange_type, exchange[i].durable, exchange[i].autoDelete);
                this.channel.exchangeDeclare(exchange[i].exchange, exchange[i].exchange_type, exchange[i].durable, exchange[i].autoDelete, null);

            } catch (java.io.IOException error) {

                logger.error("IO Error, is RabbitMQ running, check the passive/active settings!: {},{}", error.getMessage(), error.getStackTrace());
                return false;
            }
        }
        return true;
    }

    // Purges/empties all of the content on all of the queues
    //
    public boolean purge_all() {

        logger.info("Purging queues:");
        Queues[] queues = config.data.QUEUES;
        for (int i = 0; i < queues.length; i++) {
            try {
                logger.info("{}: {}", i, queues[i].queue);
                // System.out.println("Purging queue: " + queues[i].queue);
                this.channel.queuePurge(queues[i].queue);

            } catch (java.io.IOException error) {

                logger.error("IO Error, is RabbitMQ running, check the passive/active settings!: {}, {}", error.getMessage(), error.getStackTrace());
                return false;
            }
        }
        return true;
    }

    // Simple packaging of its execution methods
    //
    public void run() {
        logger.info("Running worker....");
        this.connect();
        this.subscribe();
    }
}
