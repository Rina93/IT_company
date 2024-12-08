const loginSubmit = document.querySelector("#loginModal .btn-primary");
const registerSubmit = document.querySelector("#registerModal .btn-success");
const toastContainer = document.querySelector(".toast-container");

let userId = 0;
let userRole = "unknown";

const jwt = getCookie("jwt");

if (jwt) {
  userId = getCookie("userId");
  userRole = getCookie("userRole");

  const roleMap = {
    user: "пользователя",
    company: "компании",
    admin: "администратора",
  };

  document.getElementById(
    "dashboardButton"
  ).textContent = `Личный кабинет ${roleMap[userRole]}`;

  setButtonHidden("#loginButton", true);
  setButtonHidden("#registerButton", true);
  setButtonHidden("#dashboardButton", false);
  setButtonHidden("#catalogButton", false);

  axios.defaults.headers.common["Authorization"] = `Bearer ${jwt}`;
} else {
  setButtonHidden("#loginButton", false);
  setButtonHidden("#registerButton", false);
  setButtonHidden("#dashboardButton", true);
  setButtonHidden("#catalogButton", true);
}

if (loginSubmit) {
  loginSubmit.addEventListener("click", login);
}

if (registerSubmit) {
  registerSubmit.addEventListener("click", register);
}

function setCookie(name, value) {
  const options = {
    path: "/",
    "max-age": 50000,
    secure: true, // Только для HTTPS
    samesite: "Strict", // Защита от CSRF
  };

  const cookieString =
    `${name}=${encodeURIComponent(value)};` +
    Object.entries(options)
      .map(([key, val]) => (val === true ? key : `${key}=${val}`))
      .join("; ");

  document.cookie = cookieString;
  axios.defaults.headers.common["Authorization"] = `Bearer ${value}`;
}

function getCookie(cookieName) {
  const cookies = document.cookie.split("; ");
  const cookie = cookies.find((row) => row.startsWith(`${cookieName}=`));
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
    setCookie("jwt", token.data.access_token);
    setCookie("userId", token.data.id);
    setCookie("userRole", token.data.role);
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
    return;
  }

  notify("Авторизация прошла успешно!");

  setTimeout(() => window.location.reload(), 1500);
}

async function register(e) {
  const name = document.querySelector("#registerName").value;
  const email = document.querySelector("#registerEmail").value;
  const password = document.querySelector("#registerPassword").value;
  const isCompany = document.querySelector("#registerRole").checked;
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
      is_company: isCompany,
    });
    document.querySelector("#registerModal button").click();

    notify("Регистрация прошла успешно!");
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
}

function logout() {
  document.cookie = `jwt=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; secure; samesite=Strict`;
  document.cookie = `userRole=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; secure; samesite=Strict`;
  document.cookie = `userId=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; secure; samesite=Strict`;
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
