document.addEventListener("DOMContentLoaded", function () {
  const passwordModal = document.getElementById("passwordModal");
  if (!passwordModal) return; // Evita rodar se o modal não existe

  const openPasswordModal = document.getElementById("openPasswordModal");
  const passwordModalClose = document.getElementById("passwordModalClose");
  const passwordForm = document.getElementById("passwordForm");

  const currentPasswordInput = document.getElementById("current_password");
  const newPasswordInput = document.getElementById("new_password");
  const confirmPasswordInput = document.getElementById("confirm_password");

  const modalAtualizarBtn = document.getElementById("modalAtualizarBtn");

  const currentPasswordFeedback = document.getElementById(
    "currentPasswordFeedback"
  );
  const newPasswordFeedback = document.getElementById("newPasswordFeedback");
  const confirmPasswordFeedback = document.getElementById(
    "confirmPasswordFeedback"
  );

  const reqLength = document.getElementById("req-length");
  const reqLetter = document.getElementById("req-letter");
  const reqNumber = document.getElementById("req-number");

  let currentPasswordValid = false;
  let newPasswordValid = false;
  let confirmPasswordValid = false;

  function clearAllFeedbacks() {
    [
      currentPasswordFeedback,
      newPasswordFeedback,
      confirmPasswordFeedback,
    ].forEach((el) => {
      el.textContent = "";
      el.className = "input-feedback";
    });
    [reqLength, reqLetter, reqNumber].forEach((el) => (el.className = ""));

    currentPasswordValid = false;
    newPasswordValid = false;
    confirmPasswordValid = false;
  }

  function checkPasswordRequirements(password) {
    const requirements = {
      length: password.length >= 6,
      letter: /[a-zA-Z]/.test(password),
      number: /[0-9]/.test(password),
    };

    reqLength.className = requirements.length ? "requirement-met" : "";
    reqLetter.className = requirements.letter ? "requirement-met" : "";
    reqNumber.className = requirements.number ? "requirement-met" : "";

    return requirements.length && requirements.letter && requirements.number;
  }

  function updateButtonState() {
    modalAtualizarBtn.disabled = !(
      currentPasswordValid &&
      newPasswordValid &&
      confirmPasswordValid
    );
  }

  currentPasswordInput.addEventListener("input", function () {
    currentPasswordValid = false;
    currentPasswordFeedback.textContent = "";
    updateButtonState();
  });

  currentPasswordInput.addEventListener("blur", function () {
    const senha = currentPasswordInput.value.trim();
    if (!senha) {
      currentPasswordFeedback.textContent = "Preencha a senha atual.";
      currentPasswordFeedback.className = "input-feedback error-feedback";
      currentPasswordValid = false;
      updateButtonState();
      return;
    }

    currentPasswordFeedback.textContent = "Verificando...";
    currentPasswordFeedback.className = "input-feedback";

    const validateURL = passwordModal.dataset.validateUrl;

    fetch(validateURL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: senha }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.valid) {
          currentPasswordFeedback.textContent = "✓";
          currentPasswordFeedback.className = "input-feedback success-feedback";
          currentPasswordValid = true;
        } else {
          currentPasswordFeedback.textContent = "Senha atual incorreta.";
          currentPasswordFeedback.className = "input-feedback error-feedback";
          currentPasswordValid = false;
        }
        updateButtonState();
      })
      .catch(() => {
        currentPasswordFeedback.textContent = "Erro ao validar a senha.";
        currentPasswordFeedback.className = "input-feedback error-feedback";
        currentPasswordValid = false;
        updateButtonState();
      });
  });

  newPasswordInput.addEventListener("input", function () {
    const senha = newPasswordInput.value.trim();
    const atual = currentPasswordInput.value.trim();
    const conf = confirmPasswordInput.value.trim();

    const requisitos = checkPasswordRequirements(senha);

    if (!senha) {
      newPasswordFeedback.textContent = "Informe uma nova senha.";
      newPasswordFeedback.className = "input-feedback error-feedback";
      newPasswordValid = false;
    } else if (!requisitos) {
      newPasswordFeedback.textContent = "A senha não atende aos requisitos.";
      newPasswordFeedback.className = "input-feedback error-feedback";
      newPasswordValid = false;
    } else if (senha === atual && atual !== "") {
      newPasswordFeedback.textContent =
        "A nova senha deve ser diferente da atual.";
      newPasswordFeedback.className = "input-feedback error-feedback";
      newPasswordValid = false;
    } else {
      newPasswordFeedback.textContent = "✓";
      newPasswordFeedback.className = "input-feedback success-feedback";
      newPasswordValid = true;
    }

    if (conf !== senha) {
      confirmPasswordFeedback.textContent = "As senhas não conferem.";
      confirmPasswordFeedback.className = "input-feedback error-feedback";
      confirmPasswordValid = false;
    } else if (conf && requisitos) {
      confirmPasswordFeedback.textContent = "✓";
      confirmPasswordFeedback.className = "input-feedback success-feedback";
      confirmPasswordValid = true;
    }

    updateButtonState();
  });

  confirmPasswordInput.addEventListener("input", function () {
    const conf = confirmPasswordInput.value.trim();
    const senha = newPasswordInput.value.trim();

    if (!conf) {
      confirmPasswordFeedback.textContent = "Confirme a nova senha.";
      confirmPasswordFeedback.className = "input-feedback error-feedback";
      confirmPasswordValid = false;
    } else if (conf !== senha) {
      confirmPasswordFeedback.textContent = "As senhas não conferem.";
      confirmPasswordFeedback.className = "input-feedback error-feedback";
      confirmPasswordValid = false;
    } else {
      confirmPasswordFeedback.textContent = "✓";
      confirmPasswordFeedback.className = "input-feedback success-feedback";
      confirmPasswordValid = true;
    }

    updateButtonState();
  });

  openPasswordModal.addEventListener("click", () => {
    passwordModal.style.display = "flex";
    passwordModal.classList.add("show");
    passwordForm.reset();
    clearAllFeedbacks();
    modalAtualizarBtn.disabled = true;
  });

  passwordModalClose.addEventListener("click", closeModal);
  window.addEventListener("click", (event) => {
    if (event.target === passwordModal) closeModal();
  });

  function closeModal() {
    passwordModal.classList.remove("show");
    setTimeout(() => {
      passwordModal.style.display = "none";
      passwordForm.reset();
      clearAllFeedbacks();
      modalAtualizarBtn.disabled = true;
    }, 300);
  }

  // Toggle de visibilidade dos campos de senha
  document.querySelectorAll(".toggle-password").forEach((el) => {
    el.addEventListener("click", function () {
      const inputId = el.getAttribute("onclick").match(/'([^']+)'/)[1];
      const input = document.getElementById(inputId);
      const eyeVisible = el.querySelector(".eye-visible");
      const eyeHidden = el.querySelector(".eye-hidden");

      if (input.type === "password") {
        input.type = "text";
        eyeVisible.style.display = "none";
        eyeHidden.style.display = "block";
      } else {
        input.type = "password";
        eyeVisible.style.display = "block";
        eyeHidden.style.display = "none";
      }
    });
  });
});
