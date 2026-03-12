let id = new URL(document.location).searchParams.get("id");
let isEditing = false;
let hideReviews = false;

if (id) {
  loadInfo();
} else {
  document.getElementById("editButton").hidden = false;
  document.getElementById("editButton").click();
}

async function loadInfo() {
  let company = {};
  try {
    company = (await axios.get("/companies/" + id)).data;
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
    return;
  }

  if (userRole == "admin" || userId == company.user_id) {
    document.getElementById("editButton").hidden = false;
  }

  if (userId == company.user_id) {
    hideReviews = true;
  }

  document.querySelector("#companyName").innerHTML = company.name;
  document.querySelector("#companyDescription").innerHTML = company.description;
  document.querySelector("#companyPhone").innerHTML = company.phone_number;
  document.querySelector("#companyEmail").innerHTML = company.email;
  document.querySelector("#webSiteLink").href = company.site;
  document.querySelector("#webSiteLink").innerHTML = company.site;

  document.querySelector("#companyServices").innerHTML = company.services
    .map(
      (s) =>
        `<li><input type="hidden" value="${s.id}"/><span class="serviceName">${s.name}</span> (<span class="servicePrice">${s.price}</span> руб.) <button class="btn btn-danger btn-sm delete-service-btn" hidden onclick="deleteService(this)">X</button></li>`
    )
    .join("");

  document.querySelector("#companyProjects").innerHTML = company.projects
    .map(
      (p) => `<div class="project-card col-12 col-md-4">
                    <div class="card">
                      <img src="images/project-logo.png" class="card-img-top project-logo" alt="Проект">
                      <div class="card-body">
                          <input type="hidden" value="${p.id}"/>
                          <h5 class="card-title">${p.name}</h5>
                          <p class="card-text">${p.description}</p>
                          <button class="btn btn-danger btn-sm delete-project-btn" onclick="deleteProjectItem(this)" hidden>X</button>
                      </div>
                    </div>
                </div>`
    )
    .join("");

  renderReviews(company.reviews);
}

document
  .getElementById("sendReview")
  .addEventListener("click", async function () {
    const review = document.getElementById("reviewText").value;
    const rating = document.getElementById("rating").value;

    if (!review) {
      notify("Текст отзыва должен быть заполнен", "error");
      return;
    }
    if (!rating) {
      notify("Выберите оценку", "error");
      return;
    }

    try {
      await axios.post(`/companies/${id}/reviews`, {
        content: review,
        rating: Number(rating),
      });
    } catch (e) {
      notify(e.response.data.detail ?? e.response.data, "error");
      return;
    }

    notify("Отзыв успешно добавлен");
    await loadReviews();
  });

async function toggleEditMode() {
  const editButton = document.getElementById("editButton");
  const description = document.getElementById("companyDescription");
  const name = document.getElementById("companyName");
  const contactInfoItems = document.querySelectorAll(
    "#companyPhone, #companyEmail, #webSiteLink"
  );
  const servicesList = document.querySelectorAll(".serviceName, .servicePrice"); // Услуги
  const projectCards = document.querySelectorAll(
    "#companyProjects .card-title, #companyProjects .card-text"
  ); // Портфолио
  const addServiceButton = document.getElementById("addServiceButton");
  const addProjectButton = document.getElementById("addProjectButton");
  const deleteProfileButton = document.getElementById("deleteProfileButton");
  const serviceDeleteButtons = document.querySelectorAll(".delete-service-btn");
  const projectDeleteButtons = document.querySelectorAll(".delete-project-btn");

  if (!isEditing) {
    // Включаем режим редактирования
    editButton.textContent = "Сохранить";

    // Делаем редактируемыми элементы
    description.contentEditable = "true";
    name.contentEditable = "true";
    contactInfoItems.forEach((item) => (item.contentEditable = "true"));
    servicesList.forEach((item) => {
      item.classList.add("minw-5");
      item.contentEditable = "true";
    });
    projectCards.forEach((item) => (item.contentEditable = "true"));

    // Добавляем стили для визуального указания редактируемых полей
    description.style.border = "1px solid #ccc";
    name.style.border = "1px solid #ccc";
    contactInfoItems.forEach((item) => (item.style.border = "1px solid #ccc"));
    servicesList.forEach((item) => (item.style.border = "1px solid #ccc"));
    projectCards.forEach((item) => (item.style.border = "1px solid #ccc"));

    // Показываем кнопки "Добавить" и "Удалить профиль"
    addServiceButton.hidden = false;
    addProjectButton.hidden = false;
    deleteProfileButton.hidden = false;

    // Показываем крестики для удаления
    serviceDeleteButtons.forEach((button) => (button.hidden = false));
    projectDeleteButtons.forEach((button) => (button.hidden = false));
  } else {
    let company = {
      name: name.textContent,
      description: description.textContent,
      staff: 0,
      email: document.getElementById("companyEmail").textContent,
      phone_number: document.getElementById("companyPhone").textContent,
      inn: "",
      site: document.getElementById("webSiteLink").textContent,
      services: Array.from(
        document.querySelectorAll("#companyServices > li")
      ).map((li) => {
        const id = li.querySelector("input[type=hidden]").value;

        const service = {
          price: Number(li.querySelector(".servicePrice").textContent),
          name: li.querySelector(".serviceName").textContent,
        };

        if (id) service.id = Number(id);
        return service;
      }),
      projects: Array.from(
        document.querySelectorAll("#companyProjects .card-body")
      ).map((card) => {
        const id = card.querySelector("input[type=hidden]").value;

        const project = {
          description: card.querySelector(".card-text").textContent,
          name: card.querySelector(".card-title").textContent,
        };

        if (id) project.id = Number(id);

        return project;
      }),
    };

    if (id) company.id = Number(id);

    if (!company.name) {
      notify("Название компании должно быть заполнено", "error");
      return;
    }

    if (!company.email) {
      notify("Почта должна быть заполнена", "error");
      return;
    }

    if (company.services.some((s) => !s.name)) {
      notify("Названия услуг должны быть заполнены", "error");
      return;
    }

    if (company.projects.some((p) => !p.name)) {
      notify("Названия проектов должны быть заполнены", "error");
      return;
    }

    try {
      let result = await axios.post(`/companies`, company);
      notify(result.data.message);

      if (!id) {
        id = result.data.id;
        let url = new URL(window.location);
        url.searchParams.set("id", result.data.id);
        window.history.pushState({}, "", url);
      }
    } catch (e) {
      notify(e.response.data.detail ?? e.response.data, "error");
      return;
    }

    document.querySelector("#webSiteLink").href = company.site;

    // Сохраняем изменения
    editButton.textContent = "Редактировать";

    // Убираем редактируемость
    description.contentEditable = "false";
    name.contentEditable = "false";
    contactInfoItems.forEach((item) => (item.contentEditable = "false"));
    servicesList.forEach((item) => {
      item.classList.remove("minw-5");
      item.contentEditable = "false";
    });
    projectCards.forEach((item) => (item.contentEditable = "false"));

    // Убираем стили
    description.style.border = "none";
    name.style.border = "none";
    contactInfoItems.forEach((item) => (item.style.border = "none"));
    servicesList.forEach((item) => (item.style.border = "none"));
    projectCards.forEach((item) => (item.style.border = "none"));

    // Скрываем кнопки "Добавить" и "Удалить профиль"
    addServiceButton.hidden = true;
    addProjectButton.hidden = true;
    deleteProfileButton.hidden = true;

    // Скрываем крестики
    serviceDeleteButtons.forEach((button) => (button.hidden = true));
    projectDeleteButtons.forEach((button) => (button.hidden = true));
  }

  isEditing = !isEditing;
}

function addService() {
  const servicesList = document.getElementById("companyServices");
  const newService = document.createElement("li");
  newService.innerHTML = `<input type="hidden" /><span contenteditable="true" style="border: 1px solid #ccc;" class="serviceName minw-5">Новая услуга</span> (<span style="border: 1px solid #ccc;" class="servicePrice minw-5" contentEditable="true">0</span> руб.)
     <button class="btn btn-danger btn-sm delete-service-btn" onclick="deleteService(this)">X</button></li>`;
  servicesList.appendChild(newService);
}

function deleteService(button) {
  const serviceItem = button.parentElement;

  if (
    serviceItem.querySelector("input[type=hidden]").value &&
    !confirm(
      `Вы уверены, что хотите удалить услугу "${
        serviceItem.querySelector(".serviceName").textContent
      }"?`
    )
  ) {
    return;
  }

  serviceItem.remove();
}

function addProjectItem() {
  const projectList = document.getElementById("companyProjects");
  const newProjectItem = document.createElement("div");
  newProjectItem.classList.add("col-12", "col-md-4", "project-card");
  newProjectItem.innerHTML = `
        <div class="card">
            <img src="images/project-logo.png" class="card-img-top project-logo" alt="Проект">
            <div class="card-body">
                <input type="hidden"/>
                <h5 class="card-title" contenteditable="true" style="border: 1px solid #ccc;" >Новый проект</h5>
                <p class="card-text" contenteditable="true" style="border: 1px solid #ccc;" >Описание нового проекта.</p>
                <button class="btn btn-danger btn-sm delete-project-btn" onclick="deleteProjectItem(this)">X</button>
            </div>
        </div>
    `;
  projectList.appendChild(newProjectItem);
}

function deleteProjectItem(button) {
  const card = button.closest(".project-card");
  if (
    card.querySelector("input[type=hidden]").value &&
    !confirm(
      `Вы уверены, что хотите удалить проект "${
        card.querySelector(".card-title").textContent
      }"?`
    )
  ) {
    return;
  }
  card.remove();
}

async function deleteProfile() {
  if (!confirm("Вы уверены, что хотите удалить профиль?")) return;

  try {
    await axios.delete(`/companies/${id}`);
    notify("Профиль успешно удален");
    setTimeout(() => (location.href = "catalog.html"), 1500);
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
}

async function loadReviews() {
  let reviews = [];
  try {
    reviews = (await axios.get("/companies/" + id + "/reviews")).data;
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
    return;
  }

  renderReviews(reviews);
}

function renderReviews(reviews) {
  document.querySelector("#companyReviews").innerHTML = reviews
    .map(
      (r) => `<div class="col-12 col-md-6 col-lg-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h5 class="card-title">${r.user_name}</h5>
                    <p class="card-text">
                       ${r.content}
                    </p>
                    <div class="d-flex align-items-center">
                        <span class="me-2 text-warning">
                            ${new Array(r.rating).fill(
                              '<i class="bi bi-star-fill"></i>'
                            )}
                        </span>
                        <small class="text-muted">${r.rating}/5</small>
                    </div>
                    <div class="d-flex mt-3">
                        ${
                          userId == r.user_id || userRole == "admin"
                            ? `<button onclick="deleteReview(${r.id})" class="btn btn-danger delete-comment-btn">Удалить</button>`
                            : ""
                        }
                    </div>
                </div>
            </div>
        </div>`
    )
    .join("");

  document.getElementById("reviewSection").hidden =
    hideReviews || reviews.find((r) => r.user_id == userId);
}

async function deleteReview(reviewId) {
  if (!confirm("Вы уверены, что хотите удалить отзыв?")) return;

  try {
    await axios.delete(`/companies/${id}/reviews/${reviewId}`);
    notify("Отзыв успешно удален");
    await loadReviews();
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
}
