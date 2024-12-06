const id = new URL(document.location).searchParams.get("id");
loadInfo();

async function loadInfo() {
  let company = {};
  try {
    company = (await axios.get("/companies/" + id)).data;
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
    return;
  }

  document.querySelector("#companyName").innerHTML = company.name;
  document.querySelector("#companyDescription").innerHTML = company.description;
  document.querySelector("#companyPhone").innerHTML = company.phone_number;
  document.querySelector("#companyEmail").innerHTML = company.email;
  document.querySelector("#companyServices").innerHTML = company.services
    .map((s) => `<li>${s.name} (${s.price} руб.)</li>`)
    .join("");

  document.querySelector("#companyProjects").innerHTML = company.projects
    .map(
      (p) => `<div class="col-12 col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">${p.name}</h5>
                            <p class="card-text">${p.description}</p>
                        </div>
                    </div>
                </div>`
    )
    .join("");

  document.querySelector("#companyReviews").innerHTML = company.reviews
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
                              company.current_user_id === r.user_id ||
                              company.is_admin
                                ? `<button onclick="deleteReview(${r.id})" class="btn btn-danger delete-comment-btn">Удалить</button>`
                                : ""
                            }
                        </div>
                    </div>
                </div>
            </div>`
    )
    .join("");

  document.getElementById("reviewSection").hidden = company.reviews.find(
    (r) => r.user_id == company.current_user_id
  );
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

      notify("Отзыв успешно добавлен");
      await loadInfo();
    } catch (e) {
      notify(e.response.data.detail ?? e.response.data, "error");
    }
  });

async function deleteReview(reviewId) {
  try {
    await axios.delete(`/companies/${id}/reviews/${reviewId}`);
    notify("Отзыв успешно удален");
    await loadInfo();
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
}
