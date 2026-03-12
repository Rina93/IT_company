let serviceFilters = [];
const getServicesTask = axios.get("/services");

const renderMap = (units) => {
  if (units === 1) return "отзыв";
  if ([2, 3, 4].includes(units)) return "отзыва";
  return "отзывов";
};

let searchButton = document.querySelector("#searchButton");
searchButton.addEventListener("click", loadCompanies);

loadCompanies();
loadServiceFilters();

async function loadServiceFilters() {
  try {
    serviceFilters = await getServicesTask;
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
  }
  document.getElementById(
    "serviceInput"
  ).innerHTML = `<option value="">Все услуги</option>
                  ${serviceFilters.data
                    .map((s) => `<option>${s.name}</option>`)
                    .join("")}`;
}

async function loadCompanies() {
  let filters = getFilters();
  let companies = [];

  try {
    companies = await axios.get("/companies", { params: filters });
  } catch (e) {
    notify(e.response.data.detail ?? e.response.data, "error");
    return;
  }

  await renderCompanies(companies);
}

async function renderCompanies(companies) {
  document.getElementById("company-container").innerHTML = companies.data
    .map(
      (c) => `<div class="col-12">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="maxw-7">
                      <h5 class="card-title mb-1">${c.name}</h5>
                      <img src="images/mini-logo.png" alt="Логотип компании" class="img-fluid me-3 mini-logo">
                    </div>
                    <div>
                        <button class="btn btn-outline-primary btn-sm me-2" onclick="openCompany(${
                          c.id
                        })">Посмотреть профиль</button>
                        <button onclick="visitSite('${
                          c.site
                        }')" class="btn btn-outline-secondary btn-sm">Посетить веб-сайт</button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-3">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-warning text-dark me-2">${
                              c.rating
                            }</span>
                            <span class="text-muted">${
                              c.review_count
                            } ${renderMap(c.review_count % 10)}</span>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between mb-3">
                        <div class="text-muted">Минимальная стоимость услуги: <strong>${
                          c.min_price
                        } руб.</strong></div>
                    </div>
                    <p class="card-text">
                        ${c.description}
                    </p>
                </div>
            </div>
        </div>`
    )
    .join("");
}

function getFilters() {
  let filters = {};

  const name = document.querySelector("#companyNameInput").value;
  if (name) filters.company_name = name;

  const service = document.querySelector("#serviceInput").value;
  if (service) filters.service_name = service;

  const rating = document.querySelector("#ratingInput").value;
  if (rating) filters.min_rating = rating;

  const price = document.querySelector("#priceInput").value;
  if (price) filters.max_price = price;

  return filters;
}

function openCompany(id) {
  location.href = `company.html?id=${id}`;
}

function visitSite(site) {
  window.open(site, "_blank");
}
