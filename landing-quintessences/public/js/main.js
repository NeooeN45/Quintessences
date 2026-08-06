const API_VERIFY_URL = "https://api.quintessences-platform.com/api/v1/auth/turnstile/verify";

function getTurnstileToken() {
  const input = document.querySelector('input[name="cf-turnstile-response"]');
  return input?.value?.trim() ?? "";
}

function showFeedback(message, isError) {
  const feedback = document.getElementById("form-feedback");
  if (!feedback) return;
  feedback.textContent = message;
  feedback.className = `form-feedback ${isError ? "error" : "success"}`;
}

async function verifyTurnstile(token) {
  if (!token) {
    throw new Error("Veuillez valider le défi Turnstile.");
  }
  const response = await fetch(API_VERIFY_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const data = await response.json();
  if (!response.ok || !data.valid) {
    throw new Error("Vérification Turnstile échouée.");
  }
}

async function handleSubmit(event) {
  event.preventDefault();
  const token = getTurnstileToken();
  try {
    await verifyTurnstile(token);
    showFeedback("Merci. Votre message est en file d’attente d’intégration.", false);
  } catch (err) {
    showFeedback(err.message, true);
  }
}

document.getElementById("contact-form")?.addEventListener("submit", handleSubmit);
