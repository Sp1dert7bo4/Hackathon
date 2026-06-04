const promptInput = document.querySelector("#prompt");
const sendButton = document.querySelector("#sendButton");
const statusBox = document.querySelector("#status");
const questionsBox = document.querySelector("#questions");
const resultsBox = document.querySelector("#results");
const intentBox = document.querySelector("#intentBox");
const simulateFailure = document.querySelector("#simulateFailure");
const steps = Array.from(document.querySelectorAll("#steps li"));

let lastIntent = null;
let shownRestaurantIds = [];

function setStep(name) {
  steps.forEach((step) => {
    step.classList.toggle("active", step.textContent.toLowerCase() === name.toLowerCase());
  });
}

function setStatus(message, type = "") {
  statusBox.hidden = !message;
  statusBox.textContent = message || "";
  statusBox.className = `status ${type}`.trim();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function money(value) {
  return `${Number(value).toLocaleString("vi-VN")}đ`;
}

function renderQuestions(data) {
  resultsBox.innerHTML = "";
  questionsBox.hidden = false;
  questionsBox.innerHTML = `
    <strong>Mình cần thêm một chút thông tin:</strong>
    ${data.questions.map((question) => `
      <div class="question-row">
        <span>${question}</span>
        <input aria-label="${question}" placeholder="Nhập câu trả lời" />
      </div>
    `).join("")}
    <button class="primary" id="clarifyButton">Bổ sung và tìm quán</button>
  `;
  document.querySelector("#clarifyButton").addEventListener("click", () => {
    const additions = Array.from(questionsBox.querySelectorAll("input"))
      .map((input) => input.value.trim())
      .filter(Boolean)
      .join(" ");
    promptInput.value = `${promptInput.value.trim()} ${additions}`.trim();
    runChat();
  });
}

function renderResults(data) {
  questionsBox.hidden = true;
  questionsBox.innerHTML = "";
  shownRestaurantIds = data.ranked_restaurants.map((item) => item.restaurant.id);

  if (data.warning) {
    setStatus(data.warning, "warning");
  } else if (data.explanation) {
    setStatus(data.explanation);
  } else {
    setStatus("");
  }

  if (!data.ranked_restaurants.length) {
    resultsBox.innerHTML = `<section class="status error">Không tìm được quán phù hợp. Bạn thử đổi món, khu vực hoặc ngân sách nhé.</section>`;
    return;
  }

  resultsBox.innerHTML = data.ranked_restaurants.map((item) => {
    const restaurant = item.restaurant;
    return `
      <article class="restaurant">
        <img src="${restaurant.image_url}" alt="${restaurant.name}" />
        <div class="restaurant-body">
          <div class="restaurant-head">
            <h3>${item.rank}. ${restaurant.name}</h3>
            <span class="score">${Math.round(item.score * 100)} điểm</span>
          </div>
          <div class="meta">
            <span class="pill">${restaurant.rating} sao</span>
            <span class="pill">${restaurant.distance_km} km</span>
            <span class="pill">${money(restaurant.price_min)} - ${money(restaurant.price_max)}</span>
            <span class="pill">${restaurant.district}</span>
          </div>
          <div class="reason">
            ${item.reasons.map((reason) => `<span>${reason}</span>`).join("")}
          </div>
          <div class="feedback-row">
            <button data-feedback="chosen">Chọn quán</button>
            <button data-feedback="Quá xa">Quá xa</button>
            <button data-feedback="Quá đắt">Quá đắt</button>
            <button data-feedback="Rating thấp">Rating thấp</button>
            <button data-feedback="Không hợp khẩu vị">Không hợp khẩu vị</button>
          </div>
        </div>
      </article>
    `;
  }).join("");

  resultsBox.querySelectorAll("[data-feedback]").forEach((button) => {
    button.addEventListener("click", () => handleFeedback(button.dataset.feedback));
  });
}

async function runChat() {
  const text = promptInput.value.trim();
  if (!text) {
    setStatus("Bạn nhập yêu cầu trước nhé.", "warning");
    return;
  }

  sendButton.disabled = true;
  setStep("Intent");
  setStatus("Đang phân tích yêu cầu...");
  resultsBox.innerHTML = "";

  try {
    const data = await postJson("/api/chat", {
      text,
      simulate_failure: simulateFailure.checked,
    });
    lastIntent = data.intent;
    intentBox.textContent = JSON.stringify(data.intent, null, 2);

    if (data.status === "needs_clarification") {
      setStep("Clarification");
      setStatus(`Độ tin cậy ${Math.round(data.intent.confidence * 100)}%, cần hỏi thêm.`);
      renderQuestions(data);
      return;
    }

    setStep(data.ranked_restaurants.length ? "Explain" : "Search");
    renderResults(data);
  } catch (error) {
    setStatus(`Có lỗi khi gọi API: ${error.message}`, "error");
  } finally {
    sendButton.disabled = false;
  }
}

async function handleFeedback(feedback) {
  if (feedback === "chosen") {
    setStatus("Tuyệt, mình đã ghi nhận lựa chọn của bạn.");
    setStep("Feedback");
    return;
  }
  if (!lastIntent) {
    return;
  }

  setStep("Feedback");
  setStatus("Mình đang re-rank theo phản hồi của bạn...");
  try {
    const data = await postJson("/api/feedback", {
      user_id: "demo-user",
      feedback,
      reason: feedback,
      last_intent: lastIntent,
      shown_restaurant_ids: shownRestaurantIds,
    });
    renderResults({
      ranked_restaurants: data.ranked_restaurants,
      explanation: data.explanation,
      warning: data.next_action === "ask_more" ? "Mình đã loại các quán vừa hiển thị. Bạn có thể nhập thêm khẩu vị cụ thể để lọc tốt hơn." : null,
    });
  } catch (error) {
    setStatus(`Không xử lý được feedback: ${error.message}`, "error");
  }
}

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    promptInput.value = button.dataset.prompt;
    promptInput.focus();
  });
});

sendButton.addEventListener("click", runChat);
promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    runChat();
  }
});
