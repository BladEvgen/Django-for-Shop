const roomName = JSON.parse(
  document.getElementById("json-roomname").textContent
);
const userName = JSON.parse(
  document.getElementById("json-username").textContent
);
const Token = JSON.parse(document.getElementById("json-token").textContent);
const chatSocket = new WebSocket(
  "ws://" + window.location.host + "/ws/chat/" + roomName + "/?token=" + Token
);
const messageInputDom = document.querySelector("#chat-message-input");
const messageSubmitButton = document.querySelector("#chat-message-submit");

let dataMessages = {
  avafiruser: "",
  avasecuser: "",
  firusername: "",
  secusername: "",
};

messageInputDom.addEventListener("input", function () {
  const message = messageInputDom.value.trim();
  messageSubmitButton.disabled = message === "";
});

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  console.log("Message received:", data);

  if (data.message && data.message.trim() !== "") {
    const isCurrentUser = data.username === userName;
    const isSecUserMessage = data.secusername === userName;

    const htmlRaw = `<div class="flex ${
      isCurrentUser || isSecUserMessage ? "flex-row-reverse" : "flex-row"
    } gap-x-2">
            <div class="flex flex-col rounded-xl gap-y-2 p-2 ${
              isCurrentUser || isSecUserMessage
                ? "bg-violet-300"
                : "bg-gray-200"
            }">
                <div class="flex flex-row gap-x-3">
                    <span class="font-bold">${data.username}</span>
                </div>
                <span>${data.message}</span>
            </div>
        </div>`;

    document.querySelector("#chat-messages").innerHTML += htmlRaw;
    scrollToBottom();
  }
};

chatSocket.onclose = function (e) {
  console.log("WebSocket closed:", e);
  console.log("Bye!");
};

document.querySelector("#chat-message-submit").onclick = sendMessage;

document
  .querySelector("#chat-message-input")
  .addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

function sendMessage() {
  const message = messageInputDom.value.trim();

  if (message !== "") {
    chatSocket.send(
      JSON.stringify({
        message: message,
        username: userName,
        room: roomName,
        avafiruser: dataMessages["avafiruser"],
        avasecuser: dataMessages["avasecuser"],
        firusername: dataMessages["firusername"],
        secusername: dataMessages["secusername"],
      })
    );
  }

  messageInputDom.value = "";
  messageSubmitButton.disabled = true;
  return false;
}

function scrollToBottom() {
  const objDiv = document.querySelector("#chat-messages");
  objDiv.scrollTop = objDiv.scrollHeight;
}

window.onload = function () {
  scrollToBottom();
  const dataMessagesElem = document.getElementById("chat-messages");
  dataMessages = dataMessagesElem.dataset;
};
