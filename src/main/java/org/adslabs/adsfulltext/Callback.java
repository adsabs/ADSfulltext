//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is meant to be passed to basicConsume method of the RabbitMQ Java implementation. This pattern
// creates a callback based on the DefaultConsumer, where you override the handleDelivery method. Unfortunately,
// nothing seems to work correctly if you place any calls before the basicAck method call. It seemingly fails,
// and redelivers the message to the queue it got it from. Therefore, it is kept here for reference in case it
// is required in the future.
//
package org.adslabs.adsfulltext;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.DefaultConsumer;
import com.rabbitmq.client.Envelope;
import com.rabbitmq.client.AMQP;

public class Callback extends DefaultConsumer {

    Channel ch;

    // Constructor
    //
    public Callback(Channel inputChannel) {
        super(inputChannel);
        this.ch = inputChannel;
        }

    // Override the handleDelivery method
    @Override
    public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) throws java.io.IOException {

        // Constant strings
        //
        String exchangeName = "FulltextExtractionExchange";
        String routingKey = "WriteMetaFileRoute";

        String contentType = properties.getContentType();
        long deliveryTag = envelope.getDeliveryTag();
        // (process the message components here ...)

        // This line does not work:
        //this.ch.basicPublish(exchangeName, routingKey, null, body);
        System.out.println("Going to ACK");
        this.ch.basicAck(deliveryTag, false);
        }
}