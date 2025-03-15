(() => {
  const RECONNECT_INTERVAL = 3000;
  const MAX_RECONNECT_ATTEMPTS = 5;
  const MESSAGE_BATCH_SIZE = 20;
  const SCROLL_THRESHOLD = 100;

  let reconnectAttempts = 0;
  let chatSocket = null;
  let isConnected = false;
  let messageQueue = [];
  let isTyping = false;
  let typingTimeout = null;
  let isLoadingHistory = false;
  let allHistoryLoaded = false;
  let lastMessageTimestamp = null;

  const elements = {
    roomName: JSON.parse(document.getElementById("json-roomname").textContent),
    userName: JSON.parse(document.getElementById("json-username").textContent),
    token: JSON.parse(document.getElementById("json-token").textContent),
    messageInput: document.querySelector("#chat-message-input"),
    messageSubmit: document.querySelector("#chat-message-submit"),
    chatMessages: document.querySelector("#chat-messages"),
    chatContainer: document.querySelector("#chat-container"),
    connectionStatus: document.querySelector("#connection-status"),
    loadMoreButton: document.querySelector("#load-more-messages"),
    scrollUpIndicator: document.querySelector("#scroll-up-indicator"),
    scrollDownIndicator: document.querySelector("#scroll-down-indicator"),
  };

  const messageData = {
    avafiruser: elements.chatMessages.dataset.avafiruser || "",
    avasecuser: elements.chatMessages.dataset.avasecuser || "",
    firusername: elements.chatMessages.dataset.firusername || "",
    secusername: elements.chatMessages.dataset.secusername || "",
    lastMessageTime: null,
  };

  // Track if we're at the bottom of the chat
  let isAtBottom = true;

  const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  const sanitizeHtml = (str) => {
    const temp = document.createElement("div");
    temp.textContent = str;
    return temp.innerHTML;
  };

  const getCurrentTime = () => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, "0")}:${String(
      now.getMinutes()
    ).padStart(2, "0")}`;
  };

  // Update the scroll indicators based on scroll position
  const updateScrollIndicators = () => {
    const { scrollTop, scrollHeight, clientHeight } = elements.chatMessages;

    // Show up indicator when not at the top
    if (scrollTop > 50 && !allHistoryLoaded) {
      elements.scrollUpIndicator.classList.add("opacity-100");
    } else {
      elements.scrollUpIndicator.classList.remove("opacity-100");
    }

    // Track if we're at the bottom (within threshold)
    isAtBottom = scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD;

    // Show down indicator when not at the bottom
    if (!isAtBottom) {
      elements.scrollDownIndicator.classList.add("opacity-100");
    } else {
      elements.scrollDownIndicator.classList.remove("opacity-100");
    }
  };

  const updateConnectionStatus = (status) => {
    if (elements.connectionStatus) {
      elements.connectionStatus.textContent = status;

      // Remove all classes first
      elements.connectionStatus.classList.remove(
        "connected",
        "disconnected",
        "connecting"
      );

      // Add appropriate class based on status
      const statusClass = status.toLowerCase().replace(/\s+/g, "-");
      if (statusClass.includes("connect")) {
        elements.connectionStatus.classList.add("connecting");
      } else if (statusClass.includes("disconnect")) {
        elements.connectionStatus.classList.add("disconnected");
      } else {
        elements.connectionStatus.classList.add("connected");
      }
    }
  };

  const setupWebSocket = () => {
    if (chatSocket) {
      chatSocket.close();
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    chatSocket = new WebSocket(
      `${protocol}//${window.location.host}/ws/chat/${elements.roomName}/?token=${elements.token}`
    );

    chatSocket.onopen = () => {
      console.log("WebSocket connected");
      isConnected = true;
      reconnectAttempts = 0;
      updateConnectionStatus("Connected");

      // Send any queued messages
      if (messageQueue.length > 0) {
        messageQueue.forEach((msg) => chatSocket.send(msg));
        messageQueue = [];
      }
    };

    chatSocket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        if (data.type === "history") {
          renderMessageBatch(data.messages);
        } else if (data.type === "rate_limit") {
          showNotification(data.error, "warning");
        } else if (data.message) {
          renderMessage(data);
        }
      } catch (error) {
        console.error("Error processing message:", error);
      }
    };

    chatSocket.onclose = (e) => {
      console.log("WebSocket closed", e);
      isConnected = false;
      updateConnectionStatus("Disconnected");

      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        updateConnectionStatus(
          `Reconnecting... (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`
        );
        setTimeout(setupWebSocket, RECONNECT_INTERVAL);
        reconnectAttempts++;
      } else {
        updateConnectionStatus("Connection failed");
        showNotification(
          "Chat connection lost. Please refresh the page.",
          "error"
        );
      }
    };

    chatSocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      updateConnectionStatus("Connection error");
    };
  };

  const renderMessage = (data) => {
    if (!data.message || data.message.trim() === "") return;

    const isCurrentUser = data.username === elements.userName;
    const messageTime = data.timestamp || getCurrentTime();

    // Save the timestamp for the most recent message
    lastMessageTimestamp = messageTime;

    let senderAvatar = "";
    if (data.username === data.firusername) {
      senderAvatar = data.avafiruser;
    } else if (data.username === data.secusername) {
      senderAvatar = data.avasecuser;
    } else {
      senderAvatar = isCurrentUser
        ? messageData.avafiruser
        : messageData.avasecuser;
    }

    const messageElement = document.createElement("div");
    messageElement.className = `flex ${
      isCurrentUser ? "flex-row-reverse" : "flex-row"
    } gap-x-2 mb-3 animate-fadeIn`;

    // Add data-timestamp attribute for history loading
    messageElement.dataset.timestamp = messageTime;

    const sanitizedMessage = sanitizeHtml(data.message);

    messageElement.innerHTML = `
      ${
        !isCurrentUser
          ? `
        <img src="${senderAvatar || "/static/media/png/user.png"}" alt="" 
             class="w-10 h-10 rounded-full object-cover shadow-sm border border-gray-200 mt-1">
      `
          : ""
      }
      
      <div class="flex flex-col max-w-[75%]">
        <div class="rounded-2xl px-4 py-3 shadow-sm ${
          isCurrentUser
            ? "bg-orange-500 text-white"
            : "bg-white border border-gray-200 text-gray-800"
        }">
          ${
            !isCurrentUser
              ? `
            <div class="flex flex-row gap-x-3 mb-1">
              <span class="font-medium text-sm text-gray-500">${data.username}</span>
            </div>
          `
              : ""
          }
          <p class="whitespace-pre-wrap break-words">${sanitizedMessage}</p>
        </div>
        <span class="text-xs text-gray-400 mt-1 px-1 ${
          isCurrentUser ? "self-end" : ""
        }">
          ${messageTime}
        </span>
      </div>
      
      ${
        isCurrentUser
          ? `
        <img src="${senderAvatar || "/static/media/png/user.png"}" 
             alt="" class="w-10 h-10 rounded-full object-cover shadow-sm border border-gray-200 mt-1">
      `
          : ""
      }
    `;

    elements.chatMessages.appendChild(messageElement);

    updateScrollIndicators();

    if (isAtBottom) {
      scrollToBottom();
    } else if (!isCurrentUser) {
      showNewMessageIndicator();
    }
  };

  const renderMessageBatch = (messages) => {
    if (!messages || messages.length === 0) {
      if (isLoadingHistory) {
        allHistoryLoaded = true;
        showNotification("No more messages to load", "info");
        if (elements.loadMoreButton) {
          elements.loadMoreButton.textContent = "No more messages";
          elements.loadMoreButton.disabled = true;
        }
      }
      isLoadingHistory = false;
      return;
    }

    // Save scroll position and height before adding messages
    const scrollPosition = elements.chatMessages.scrollTop;
    const oldScrollHeight = elements.chatMessages.scrollHeight;

    const fragment = document.createDocumentFragment();

    messages.forEach((data) => {
      if (!data.message || data.message.trim() === "") return;

      const isCurrentUser = data.username === elements.userName;
      const messageTime = data.timestamp || getCurrentTime();

      let senderAvatar = "";
      if (data.username === data.firusername) {
        senderAvatar = data.avafiruser;
      } else if (data.username === data.secusername) {
        senderAvatar = data.avasecuser;
      } else {
        senderAvatar = isCurrentUser
          ? messageData.avafiruser
          : messageData.avasecuser;
      }

      const messageElement = document.createElement("div");
      messageElement.className = `flex ${
        isCurrentUser ? "flex-row-reverse" : "flex-row"
      } gap-x-2 mb-3`;

      // Add data-timestamp attribute for history loading
      messageElement.dataset.timestamp = messageTime;

      const sanitizedMessage = sanitizeHtml(data.message);

      messageElement.innerHTML = `
        ${
          !isCurrentUser
            ? `
          <img src="${senderAvatar || "/static/media/png/user.png"}" alt="" 
               class="w-10 h-10 rounded-full object-cover shadow-sm border border-gray-200 mt-1">
        `
            : ""
        }
        
        <div class="flex flex-col max-w-[75%]">
          <div class="rounded-2xl px-4 py-3 shadow-sm ${
            isCurrentUser
              ? "bg-orange-500 text-white"
              : "bg-white border border-gray-200 text-gray-800"
          }">
            ${
              !isCurrentUser
                ? `
              <div class="flex flex-row gap-x-3 mb-1">
                <span class="font-medium text-sm text-gray-500">${data.username}</span>
              </div>
            `
                : ""
            }
            <p class="whitespace-pre-wrap break-words">${sanitizedMessage}</p>
          </div>
          <span class="text-xs text-gray-400 mt-1 px-1 ${
            isCurrentUser ? "self-end" : ""
          }">
            ${messageTime}
          </span>
        </div>
        
        ${
          isCurrentUser
            ? `
          <img src="${senderAvatar || "/static/media/png/user.png"}" 
               alt="" class="w-10 h-10 rounded-full object-cover shadow-sm border border-gray-200 mt-1">
        `
            : ""
        }
      `;

      fragment.appendChild(messageElement);
    });

    if (isLoadingHistory) {
      // Insert at the top for history loading
      if (elements.chatMessages.firstChild) {
        elements.chatMessages.insertBefore(
          fragment,
          elements.chatMessages.firstChild
        );
      } else {
        elements.chatMessages.appendChild(fragment);
      }

      // Maintain scroll position after adding content at the top
      const newScrollHeight = elements.chatMessages.scrollHeight;
      elements.chatMessages.scrollTop =
        scrollPosition + (newScrollHeight - oldScrollHeight);
    } else {
      // Append at the bottom for initial load
      elements.chatMessages.appendChild(fragment);
      scrollToBottom();
    }

    isLoadingHistory = false;
    updateScrollIndicators();
  };

  const scrollToBottom = () => {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    updateScrollIndicators();
  };

  const showNewMessageIndicator = () => {
    // Remove existing indicator if present
    const existingIndicator = document.getElementById("new-message-indicator");
    if (existingIndicator) {
      existingIndicator.remove();
    }

    const indicator = document.createElement("div");
    indicator.id = "new-message-indicator";
    indicator.textContent = "New messages ↓";
    indicator.onclick = scrollToBottom;

    document.body.appendChild(indicator);

    setTimeout(() => {
      indicator.classList.add("fade-out");
      setTimeout(() => {
        if (indicator.parentNode) {
          indicator.parentNode.removeChild(indicator);
        }
      }, 500);
    }, 5000);
  };

  const showNotification = (message, type = "info") => {
    const notification = document.createElement("div");
    notification.className = `chat-notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.classList.add("fade-out");
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 500);
    }, 5000);
  };

  const sendMessage = () => {
    const message = elements.messageInput.value.trim();

    if (message === "") return;

    const messageObject = {
      message: message,
      username: elements.userName,
      room: elements.roomName,
      avafiruser: messageData.avafiruser,
      avasecuser: messageData.avasecuser,
      firusername: messageData.firusername,
      secusername: messageData.secusername,
    };

    const messageJson = JSON.stringify(messageObject);

    if (isConnected) {
      chatSocket.send(messageJson);
    } else {
      messageQueue.push(messageJson);
      showNotification("Message queued. Waiting for connection...", "warning");
      setupWebSocket();
    }

    elements.messageInput.value = "";
    elements.messageInput.style.height = "auto";
    elements.messageInput.focus();
    elements.messageSubmit.disabled = true;

    clearTimeout(typingTimeout);
    isTyping = false;

    // Scroll to bottom when sending a message
    scrollToBottom();
  };

  const loadMoreHistory = async () => {
    if (isLoadingHistory || allHistoryLoaded) return;

    isLoadingHistory = true;

    try {
      // Update button state to show loading
      const originalButtonText = elements.loadMoreButton.innerHTML;
      elements.loadMoreButton.innerHTML = `
        <svg class="animate-spin h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading...
      `;

      // Find the first visible message timestamp
      const firstMessageTime =
        Array.from(elements.chatMessages.querySelectorAll("[data-timestamp]"))
          .map((el) => el.dataset.timestamp)
          .sort()[0] || lastMessageTimestamp;

      if (!firstMessageTime) {
        isLoadingHistory = false;
        elements.loadMoreButton.innerHTML = originalButtonText;
        return;
      }

      const response = await fetch(
        `/api/chat/${elements.roomName}/history?before=${firstMessageTime}&limit=${MESSAGE_BATCH_SIZE}&token=${elements.token}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status}`);
      }

      const data = await response.json();

      // Reset button state
      elements.loadMoreButton.innerHTML = originalButtonText;

      if (data.messages && data.messages.length > 0) {
        renderMessageBatch(data.messages);
        // If we got fewer messages than requested, we've reached the end
        if (data.messages.length < MESSAGE_BATCH_SIZE) {
          allHistoryLoaded = true;
          elements.loadMoreButton.textContent = "No more messages";
          elements.loadMoreButton.disabled = true;
        }
      } else {
        allHistoryLoaded = true;
        elements.loadMoreButton.textContent = "No more messages";
        elements.loadMoreButton.disabled = true;
      }
    } catch (error) {
      console.error("Error loading more messages:", error);
      showNotification("Failed to load more messages", "error");
      elements.loadMoreButton.innerHTML = "Try again";
      isLoadingHistory = false;
    }
  };

  const handleInput = debounce(() => {
    const isEmpty = elements.messageInput.value.trim() === "";
    elements.messageSubmit.disabled = isEmpty;

    elements.messageInput.style.height = "auto";
    elements.messageInput.style.height = `${elements.messageInput.scrollHeight}px`;

    if (!isEmpty && !isTyping) {
      isTyping = true;
      // Send typing indicator to server (optional feature)
      // chatSocket.send(JSON.stringify({type: 'typing_start', username: elements.userName}));
    } else if (isEmpty && isTyping) {
      isTyping = false;
      // Send stopped typing indicator (optional feature)
      // chatSocket.send(JSON.stringify({type: 'typing_stop', username: elements.userName}));
    }

    // Reset typing timeout
    clearTimeout(typingTimeout);
    if (!isEmpty) {
      typingTimeout = setTimeout(() => {
        isTyping = false;
        // Send stopped typing indicator (optional feature)
        // chatSocket.send(JSON.stringify({type: 'typing_stop', username: elements.userName}));
      }, 3000);
    }
  }, 100);

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!elements.messageSubmit.disabled) {
        sendMessage();
      }
    }
  };

  const initChat = () => {
    elements.messageInput.addEventListener("input", handleInput);
    elements.messageInput.addEventListener("keydown", handleKeyDown);
    elements.messageSubmit.onclick = sendMessage;

    // Add event listener for scroll to update indicators
    elements.chatMessages.addEventListener("scroll", updateScrollIndicators);

    // Add click handler for scroll down indicator
    if (elements.scrollDownIndicator) {
      elements.scrollDownIndicator.addEventListener("click", scrollToBottom);
    }

    // Load more history button
    if (elements.loadMoreButton) {
      elements.loadMoreButton.addEventListener("click", loadMoreHistory);
    }

    setupWebSocket();

    scrollToBottom();
    elements.messageSubmit.disabled = true;
    elements.messageInput.focus();

    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && !isConnected) {
        setupWebSocket();
      }
    });

    setInterval(() => {
      if (!isConnected) {
        setupWebSocket();
      }
    }, 60000);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChat);
  } else {
    initChat();
  }
})();
