import amqplib from "amqplib";

async function consumeFromMQ(amqp_url, queue, consumerTag, notify) {
  try {
    const connection = await amqplib.connect(amqp_url, "heartbeat=60");
    const channel = await connection.createChannel();
    channel.prefetch(10);

    await channel.assertQueue(queue, { durable: true });

    await channel.consume(
      queue,
      async (msg) => {
        const message = onMessageReceived(msg);
        await notify(message);
        await channel.ack(msg);
      },
      {
        noAck: false,
        consumerTag: consumerTag
      }
    );

    process.once("SIGINT", async () => {
      console.log("got sigint, closing connection");
      await channel.close();
      await connection.close();
      process.exit(0);
    });
  } catch (error) {
    console.error(error);
  }
}

function onMessageReceived(message) {
  try {
    const decodedMessage = JSON.parse(Buffer.from(message.content).toString());
    console.log("Message received from MQ");
    console.log(decodedMessage);

    return decodedMessage;
  } catch (error) {
    console.error(error);

    throw new Error("Can't read received message");
  }
}

export { consumeFromMQ };
