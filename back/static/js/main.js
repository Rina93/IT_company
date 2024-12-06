const loginSubmit = document.querySelector("#loginModal .btn-primary");
const registerSubmit = document.querySelector("#registerModal .btn-success");
const toastContainer = document.querySelector(".toast-container");

const jwt = getJWT();

if (jwt) {
  loggedIn();
  axios.defaults.headers.common["Authorization"] = `Bearer ${jwt}`;
}

if (loginSubmit) {
  loginSubmit.addEventListener("click", login);
}

if (registerSubmit) {
  registerSubmit.addEventListener("click", register);
}

function setJWT(value) {
  const options = {
    path: "/",
    "max-age": 50000,
    secure: true, // Только для HTTPS
    samesite: "Strict", // Защита от CSRF
  };

  const cookieString =
    `jwt=${encodeURIComponent(value)};` +
    Object.entries(options)
      .map(([key, val]) => (val === true ? key : `${key}=${val}`))
      .join("; ");

  document.cookie = cookieString;
  axios.defaults.headers.common["Authorization"] = `Bearer ${value}`;
}

function getJWT() {
  const cookies = document.cookie.split("; ");
  const cookie = cookies.find((row) => row.startsWith(`${"jwt"}=`));
  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

function setButtonHidden(buttonId, hidden = true) {
  const button = document.querySelector(buttonId);

  if (button) button.hidden = hidden;
}

async function login(e) {
  const email = document.querySelector("#loginEmail").value;
  const password = document.querySelector("#loginPassword").value;

  if (!email) {
    notify("Почта должна быть заполнена", "error");
    return;
  }
  if (!password) {
    notify("Пароль должен быть заполнен", "error");
    return;
  }

  try {
    let token = await axios.post(
      "/token",
      `username=${document.querySelector("#loginEmail").value}&password=${
        document.querySelector("#loginPassword").value
      }`, // данные для формы
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded", // только для получения токена
        },
      }
    );

    notify("Авторизация прошла успешно!");
    setJWT(token.data.access_token);
    setTimeout(() => window.location.reload(), 1500);
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
}

async function register(e) {
  const name = document.querySelector("#registerName").value;
  const email = document.querySelector("#registerEmail").value;
  const password = document.querySelector("#registerPassword").value;
  const confirmPassword = document.querySelector(
    "#registerConfirmPassword"
  ).value;

  if (!name) {
    notify("Имя должно быть заполнено", "error");
    return;
  }
  if (!email) {
    notify("Почта должна быть заполнена", "error");
    return;
  }
  if (!password) {
    notify("Пароль должен быть заполнен", "error");
    return;
  }
  if (password != confirmPassword) {
    notify("Пароли должны совпадать", "error");
    return;
  }

  try {
    await axios.post("/register", {
      email,
      phone_number: "",
      password,
      name,
      is_company: false,
    });
    document.querySelector("#registerModal button").click();

    notify("Регистрация прошла успешно!");
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
}

function loggedIn() {
  setButtonHidden("#loginButton", true);
  setButtonHidden("#registerButton", true);
  setButtonHidden("#dashboardButton", false);
  setButtonHidden("#catalogButton", false);
}

function logout() {
  document.cookie = `jwt=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; secure; samesite=Strict`;
  location.href = `index.html`;
}

function notify(message = "", type = "success", duration = 2000) {
  const toastTemplate = document
    .getElementById("toastTemplate")
    .cloneNode(true);

  let bgClass = "bg-primary text-white";
  let iconHTML = "ℹ️"; // Информационная иконка по умолчанию
  let title = "";

  switch (type) {
    case "success":
      title = "Операция выполнена";
      bgClass = "bg-success text-white";
      iconHTML = "✔️";
      break;
    case "error":
      title = "Ошибка!";
      bgClass = "bg-danger text-white";
      iconHTML = "❌";
      break;
  }

  // Настройка содержимого тоста
  toastTemplate.style.display = "block"; // Показываем тост
  toastTemplate.classList.add(...bgClass.split(" ")); // Добавляем классы
  toastTemplate.querySelector("#toastIcon").innerHTML = iconHTML;
  toastTemplate.querySelector("#toastTitle").textContent = title;
  toastTemplate.querySelector("#toastBody").textContent = message;

  const toast = new bootstrap.Toast(toastTemplate, { delay: duration });
  toastContainer.appendChild(toastTemplate);
  toast.show();
  toastTemplate.addEventListener("hidden.bs.toast", () => {
    toastTemplate.remove();
  });
}
