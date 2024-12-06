loadInfo();

async function loadInfo() {
  let me = {};
  try {
    me = (await axios.get("/me")).data;
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
    return;
  }

  document.querySelector("#fullName").value = me.name;
  document.querySelector("#email").value = me.email;
  document.querySelector("#phone").value = me.phone_number;
}

document
  .getElementById("editProfileButton")
  .addEventListener("click", async function () {
    const isEditing = document.getElementById("fullName").disabled;

    // Переключаем режим редактирования
    document.getElementById("fullName").disabled = !isEditing;
    document.getElementById("email").disabled = !isEditing;
    document.getElementById("phone").disabled = !isEditing;

    // Меняем текст кнопки
    if (isEditing) {
      this.textContent = "Сохранить";
      this.classList.remove("btn-primary");
      this.classList.add("btn-success");
    } else {
      this.textContent = "Редактировать";
      this.classList.remove("btn-success");
      this.classList.add("btn-primary");

      const name = document.getElementById("fullName").value;
      const email = document.getElementById("email").value;
      const phone = document.getElementById("phone").value;

      if (!name) {
        notify("Имя должно быть заполнено", "error");
        return;
      }
      if (!email) {
        notify("Почта должна быть заполнена", "error");
        return;
      }
      try {
        await axios.put("/me", {
          name,
          email,
          phone_number: phone,
        });

        notify("Данные успешно обновлены");
      } catch (e) {
        notify(e.response.data.detail ?? e.response.data, "error");
      }
    }
  });

document
  .getElementById("changePasswordButton")
  .addEventListener("click", async function () {
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (newPassword != confirmPassword) {
      notify("Пароли должны совпадать", "error");
      return;
    }

    try {
      await axios.put("/users", {
        password: newPassword,
      });

      notify("Пароль успешно изменен");
    } catch (e) {
      notify(e.response.data.detail ?? e.response.data, "error");
    }
  });
