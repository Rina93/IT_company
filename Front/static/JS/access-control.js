// Уровни доступа

// Пример инициализации роли
const currentUserRole = 'admin'; // Меняется на основе логики авторизации
setAccessLevel(currentUserRole);

const accessLevels = {
    guest: {
        canAccess: ['index.html', 'catalog.html', 'company.html', 'about.html'],
        canEdit: false,
    },
    user: {
        canAccess: ['index.html', 'catalog.html', 'company.html', 'about.html', 'Personal-account.html'],
        canEdit: ['comments'],
    },
    organization: {
        canAccess: ['index.html', 'catalog.html', 'company.html', 'about.html', 'Personal-account.html'],
        canEdit: ['comments', 'organizationProfile'],
    },
    admin: {
        canAccess: ['index.html', 'catalog.html', 'company.html', 'about.html', 'Personal-account.html', 'admin-panel.html'],
        canEdit: ['comments', 'organizationProfile', 'all'],
    },
};

// Проверка доступа
function setAccessLevel(role) {
    // Управление видимостью кнопок в шапке
    document.getElementById('dashboardButton').classList.toggle('d-none', role === 'guest');
    document.getElementById('loginButton').classList.toggle('d-none', role !== 'guest');
    document.getElementById('registerButton').classList.toggle('d-none', role !== 'guest');
    document.getElementById('adminPanelButton').classList.toggle('d-none', role !== 'admin');

    // Управление видимостью кнопки "Профиль организации"
    const organizationProfileButton = document.querySelector('a[href="company.html"]');
    if (organizationProfileButton) {
        // Скрыть кнопку, если у пользователя нет доступа к профилю организации
        if (role !== 'organization' && role !== 'admin') {
            organizationProfileButton.classList.add('d-none');
        } else {
            organizationProfileButton.classList.remove('d-none');
        }
    }
    
    // Управление доступом к страницам и разделам
    const accessiblePages = accessLevels[role].canAccess;
    const currentPage = window.location.pathname.split('/').pop(); // Получаем текущую страницу

    // Проверяем доступность страницы
    if (!accessiblePages.includes(currentPage)) {
        window.location.href = 'index.html'; // Перенаправляем на главную, если доступ запрещен
    }

    // Личный кабинет
    document.addEventListener('DOMContentLoaded', function () {
        const editProfileButton = document.getElementById('editProfileButton');
        const settingsLink = document.querySelector('a[href="#settings"]');
        const innInput = document.getElementById('inn'); // Получаем поле ИНН
        const commentEditButtons = document.querySelectorAll('.edit-comment-btn'); // Получаем все кнопки редактирования комментариев
        const commentDeleteButtons = document.querySelectorAll('.delete-comment-btn'); // Получаем все кнопки удаления комментариев

        // Редактирование профиля
        if (role === 'guest') {
            // Гостю доступна только информация, без возможности редактирования
            editProfileButton.classList.add('d-none'); // скрыть кнопку "Редактировать"
            settingsLink.classList.add('d-none'); // скрыть раздел "Настройки"
            innInput.disabled = true; // запрещаем редактирование ИНН
        } else if (role === 'user') {
            // Пользователь может редактировать только свой профиль, но ИНН остается заблокированным
            editProfileButton.classList.remove('d-none');
            settingsLink.classList.remove('d-none');
            innInput.disabled = true; // запрещаем редактирование ИНН
        } else if (role === 'organization') {
            // Организация имеет доступ к редактированию профиля и настройкам
            editProfileButton.classList.remove('d-none');
            settingsLink.classList.remove('d-none');
            innInput.disabled = false; // разрешаем редактировать ИНН
        } else if (role === 'admin') {
            // Админ имеет полный доступ
            editProfileButton.classList.remove('d-none');
            settingsLink.classList.remove('d-none');
            innInput.disabled = false; // разрешаем редактировать ИНН
        }





// Комментарии на странице организации
        // Редактирование комментариев (только для пользователей и администраторов)
        if (role === 'user' || role === 'admin') {
            commentEditButtons.forEach(function (button) {
                button.classList.remove('d-none'); // Показать кнопки редактирования комментариев
            });
            commentDeleteButtons.forEach(function (button) {
                button.classList.remove('d-none'); // Показать кнопки удаления комментариев
            });
        } else {
            commentEditButtons.forEach(function (button) {
                button.classList.add('d-none'); // Скрыть кнопки редактирования комментариев для других ролей
            });
            commentDeleteButtons.forEach(function (button) {
                button.classList.add('d-none'); // Скрыть кнопки удаления комментариев для других ролей
            });
        }

        // Обработчик для редактирования комментариев
        commentEditButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                const commentText = button.previousElementSibling;
                const newText = prompt('Редактировать комментарий:', commentText.textContent);
                if (newText) {
                    commentText.textContent = newText; // Обновляем текст комментария
                }
            });
        });

        // Обработчик для удаления комментариев
        commentDeleteButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                const commentCard = button.closest('.card');
                if (confirm('Вы уверены, что хотите удалить этот комментарий?')) {
                    commentCard.remove(); // Удаляем карточку комментария
                }
            });
        });
    });
}
