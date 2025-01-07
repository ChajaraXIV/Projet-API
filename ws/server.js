import { consumeFromMQ } from "./services/consumeFromMQ.js";
import { WebSocketServer } from "ws";

const amqp_url = process.env.AMQP_URL;
const queue = process.env.QUEUE;
const consumerTag = process.env.CONSUMER_TAG;

const wss = new WebSocketServer({ port: 3000 });

const subscribers = new Map();
//contient une référence vers chaque Utilisateur connecté au serveur WebSocket sur la base de son numéro d'id

wss.on("connection", (socket) => {
  socket.on("error", console.error);

  //réception d'un message
  socket.on("message", (message) => {
    console.log("Subscribtion received: %s", message);

    try {
      const msg = JSON.parse(message);
      const user_id = msg.user_id;

      if (msg.type === "subscribe") {
        subscribers.set(user_id, socket); //ajoute un destinataire et le référence selon son id
        const data = JSON.stringify({
          type: "subscribe",
          user_id: user_id
        });

        console.log(`User #${user_id} has been registered to WS notifications`);

        socket.send(data);
      }
    } catch (error) {
      console.error(error);
      throw new Error("Can't publish websocket message");
    }
  });
});

//emet une notification à tous les destinataires sans distinction d'id
async function notifyAll(msg) {
  try {
    const data = JSON.stringify({
      type: "notification",
      task: msg.task,
      message: msg.message
    });

    //console.log("nombre de destinataires : " + subscribers.entries.length);

    subscribers.forEach(async (client) => {
      if (!client) {
        console.log("User %s disconnected from Websocket", msg.task.user_id);
      } else {
        await client.send(data);
        console.log("Notification sent to User : %s", msg.task.user_id);
      }
    });
  } catch (error) {
    console.error(error);
  }
}

//emet une notification à un destinataire (User) sur la base de son id
function notify(msg) {
  try {
    const data = JSON.stringify({
      type: "notification",
      task: msg.task,
      message: msg.message
    });

    const user_id = msg.task.user_id;

    const client = subscribers.get(user_id);

    if (!client) {
      console.log("User %s disconnected from Websocket", msg.task.user_id);
    } else {
      client.send(data);
      console.log("Notification sent to User : %s", msg.task.user_id);
    }
  } catch (error) {
    console.error(error);
  }
}

await consumeFromMQ(amqp_url, queue, consumerTag, notify); //pour envoyer uniquement à l'abonnée dont l'identifiant correspond à l'auteur de la Task
//await consumeFromMQ(amqp_url, queue, consumerTag, notifyAll); //pour envoyer à tous les "abonnés" sans distinction
