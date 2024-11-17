// Открытие модального окна
document.getElementById('openNewModalBtn').addEventListener('click', function() {
  var myModal = new bootstrap.Modal(document.getElementById('newModal'));
  myModal.show();
});

function openCategoryFilterModal1(filterType) {
  currentCategoryFilterType = filterType;
  let filterContent = '';
  if (filterType === 'range') {
    filterContent = `
            <div class="mb-3">
                <label for="category_start_date" class="form-label">От:</label>
                <input type="date" id="category_start_date" class="form-control">
            </div>
            <div class="mb-3">
                <label for="category_end_date" class="form-label">До:</label>
                <input type="date" id="category_end_date" class="form-control">
            </div>
        `;
  } else if (filterType === 'year') {
    const currentYear = new Date().getFullYear();
    filterContent = `
            <div class="d-flex justify-content-center align-items-center">
                <button class="btn btn-secondary me-3" onclick="changeYear(-1)">←</button>
                <span id="filter_year" class="fw-bold">${currentYear}</span>
                <button class="btn btn-secondary ms-3" onclick="changeYear(1)">→</button>
            </div>
        `;
  } else if (filterType === 'month') {
    const monthNames = [
      "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ];
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    filterContent = `
            <div class="d-flex justify-content-center align-items-center">
                <button class="btn btn-secondary me-3" onclick="changeMonth(-1)">←</button>
                <span id="filter_month" class="fw-bold">${monthNames[currentMonth]} ${currentYear}</span>
                <button class="btn btn-secondary ms-3" onclick="changeMonth(1)">→</button>
            </div>
        `;
  }
  document.getElementById('filterCategoryContent').innerHTML = filterContent;
  const filterModal = new bootstrap.Modal(document.getElementById('filterCategoryModal'));
  filterModal.show();
}

function changeYear(direction) {
  const yearElement = document.getElementById('filter_year');
  let currentYear = parseInt(yearElement.textContent);
  currentYear += direction;
  yearElement.textContent = currentYear;
}

function changeMonth(direction) {
  const monthNames = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
  ];
  const monthElement = document.getElementById('filter_month');
  let [month, year] = monthElement.textContent.split(' ');
  let monthIndex = monthNames.indexOf(month);
  year = parseInt(year);
  monthIndex += direction;
  if (monthIndex < 0) {
    monthIndex = 11;
    year -= 1;
  } else if (monthIndex > 11) {
    monthIndex = 0;
    year += 1;
  }
  monthElement.textContent = `${monthNames[monthIndex]} ${year}`;
}

function positionCategories(diagramId, categoryClass) {
  const diagram = document.querySelector(`#${diagramId}`);
  if (!diagram) return;
  const categories = diagram.querySelectorAll(`.${categoryClass}`);
  const maxCategories = 16; // Максимальное количество категорий
  const visibleCategories = Array.from(categories).slice(0, maxCategories); // Ограничиваем количество категорий
  const angleStep = 360 / visibleCategories.length; // Угол между категориями
  // Временное отображение скрытого диаграммы для расчета размеров
  const wasHidden = diagram.classList.contains('hidden');
  if (wasHidden) {
    diagram.style.display = 'block';
  }
  // Определяем размеры диаграммы
  const donutChart = diagram.querySelector('.donut-chart');
  const donutChartCenterX = donutChart.offsetWidth / 2;
  const donutChartCenterY = donutChart.offsetHeight / 2;
  const radius = donutChartCenterX + 75; // Радиус от центра + отступ
  visibleCategories.forEach((category, index) => {
    const angle = index * angleStep; // Угол в градусах
    const radian = (angle * Math.PI) / 180; // Угол в радианах
    // Координаты категорий
    const x = donutChartCenterX + radius * Math.cos(radian) - category.offsetWidth / 2;
    const y = donutChartCenterY + radius * Math.sin(radian) - category.offsetHeight / 2;
    category.style.position = 'absolute';
    category.style.left = `${x}px`;
    category.style.top = `${y}px`;
  });
  // Вернуть диаграмму в изначальное состояние
  if (wasHidden) {
    diagram.style.display = '';
  }
}
// Применение для каждой диаграммы
positionCategories('incomeDiagram', 'income-category'); // Расположить категории доходов
positionCategories('expenseDiagram', 'expense-category'); // Расположить категории расходов
let currentCategoryFilterType = null;

function openCategoryFilterModal(filterType) {
  currentCategoryFilterType = filterType; // Сохраняем тип фильтра
  let filterContent = ''; // Начинаем с пустого контента
  // Проверяем тип фильтра и подготавливаем соответствующие элементы
  if (filterType === 'range') {
    filterContent = `
              <div class="mb-3">
                  <label for="category_start_date" class="form-label">От:</label>
                  <input type="date" id="category_start_date" class="form-control">
              </div>
              <div class="mb-3">
                  <label for="category_end_date" class="form-label">До:</label>
                  <input type="date" id="category_end_date" class="form-control">
              </div>
          `;
  } else if (filterType === 'year') {
    const currentYear = new Date().getFullYear();
    filterContent = `
              <div class="d-flex justify-content-center align-items-center">
                  <button class="btn btn-secondary me-3" onclick="changeYear(-1)">←</button>
                  <span id="filter_year" class="fw-bold">${currentYear}</span>
                  <button class="btn btn-secondary ms-3" onclick="changeYear(1)">→</button>
              </div>
          `;
  } else if (filterType === 'month') {
    const monthNames = [
      "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ];
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    filterContent = `
              <div class="d-flex justify-content-center align-items-center">
                  <button class="btn btn-secondary me-3" onclick="changeMonth(-1)">←</button>
                  <span id="filter_month" class="fw-bold">${monthNames[currentMonth]} ${currentYear}</span>
                  <button class="btn btn-secondary ms-3" onclick="changeMonth(1)">→</button>
              </div>
          `;
  }
  // Заполняем модальное окно контентом
  document.getElementById('filterCategoryContent').innerHTML = filterContent;
  // Показываем модальное окно
  const filterModal = new bootstrap.Modal(document.getElementById('filterCategoryModal'));
  filterModal.show();
}

function applyCategoryFilter() {
  let params = {};
  if (currentCategoryFilterType === 'range') {
    const startDate = document.getElementById('category_start_date').value;
    const endDate = document.getElementById('category_end_date').value;
    if (!startDate || !endDate) {
      alert("Укажите оба значения для диапазона!");
      return;
    }
    params = {
      start_date: startDate,
      end_date: endDate
    };
  } else if (currentCategoryFilterType === 'year') {
    const year = document.getElementById('filter_year').textContent;
    params = {
      year
    };
  } else if (currentCategoryFilterType === 'month') {
    const monthNames = [
      "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ];
    const [month, year] = document.getElementById('filter_month').textContent.split(' ');
    const monthIndex = monthNames.indexOf(month) + 1; // Преобразуем в числовое значение (1-12)
    params = {
      year,
      month: monthIndex
    }; // Отправляем числовое значение
  }
  fetch(`/api/categories/filter/?${new URLSearchParams(params)}`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateCategoryList(data.categories);
      } else {
        alert("Ошибка фильтрации!");
      }
    })
    .catch(err => {
      console.error("Ошибка:", err);
    });
}

function saveUpdatedCategoriesToDatabase(categories) {
  // Формируем данные для отправки
  const data = {
    categories
  };
  // Отправка данных на сервер для сохранения в базе данных
  fetch('/api/categories/update/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(), // Получение CSRF токена
      },
      body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        console.log('Категории успешно обновлены в базе данных');
      } else {
        alert("Ошибка при обновлении категорий в базе данных");
      }
    })
    .catch(error => {
      console.error("Ошибка:", error);
    });
}

function getCsrfToken() {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  return csrfToken;
}

function updateCategoryList(categories) {
  // Находим элемент на странице, где будут отображаться категории
  const categoryList = document.getElementById('categoryList');
  const incomeCategories = document.getElementById('incomeCategories'); // Для доходных категорий
  const expenseCategories = document.getElementById('expenseCategories'); // Для расходных категорий
  // Очищаем текущий список категорий
  categoryList.innerHTML = '';
  incomeCategories.innerHTML = '';
  expenseCategories.innerHTML = '';
  // Обрабатываем полученные категории
  categories.forEach(category => {
    const listItem = document.createElement('li');
    listItem.textContent = category.name + ': ' + category.value; // Отображаем имя и пересчитанное значение
    categoryList.appendChild(listItem);
    // Динамически обновляем категории на диаграммах (если они существуют)
    if (category.is_expense) {
      const expenseItem = document.createElement('div');
      expenseItem.classList.add('category');
      expenseItem.style.backgroundColor = category.color;
      expenseItem.textContent = category.name + ': ' + category.value;
      expenseCategories.appendChild(expenseItem);
    } else {
      const incomeItem = document.createElement('div');
      incomeItem.classList.add('category');
      incomeItem.style.backgroundColor = category.color;
      incomeItem.textContent = category.name + ': ' + category.value;
      incomeCategories.appendChild(incomeItem);
    }
  });
}

function getCsrfToken() {
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') return value;
  }
  return '';
}
// Обработчик формы редактирования категории через AJAX
document.getElementById("editCategoryForm").addEventListener("submit", function(event) {
  event.preventDefault(); // Останавливаем стандартное поведение формы
  const formData = new FormData(this);
  const categoryName = document.getElementById("editCategoryName").value; // Получаем название категории для обновления
  fetch(`/api/category/${categoryName}/update/`, {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
      },
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Закрытие модального окна и обновление страницы
        document.getElementById("editCategoryModal").style.display = "none";
        window.location.reload(); // Обновление страницы для отображения измененных данных
      } else {
        alert(data.error || "Ошибка при сохранении изменений!");
      }
    })
    .catch(error => {
      console.error("Ошибка:", error);
    });
});
// Открытие модального окна для редактирования категории
function openEditCategoryModal(categoryName) {
  if (!categoryName) {
    console.error("Имя категории отсутствует.");
    return;
  }
  // Получаем данные категории через AJAX
  fetch(`/api/category/${categoryName}/`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Заполняем модальное окно данными категории
        document.getElementById("editCategoryName").value = data.category.name;
        document.getElementById("editCategoryColor").value = data.category.color;
        // Отображаем модальное окно
        document.getElementById("editCategoryModal").style.display = "block";
      } else {
        console.error("Ошибка при получении данных категории:", data.error);
      }
    })
    .catch(error => {
      console.error("Ошибка:", error);
    });
}
// Удаление категории через AJAX
document.getElementById("deleteCategoryBtn").addEventListener("click", function() {
  const categoryName = document.getElementById("editCategoryName").value;
  if (confirm(`Вы уверены, что хотите удалить категорию "${categoryName}"?`)) {
    fetch(`/api/category/${categoryName}/delete/`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Убираем категорию и обновляем интерфейс
          window.location.reload();
        }
      })
      .catch(error => console.error("Ошибка:", error));
  }
});
// Открытие модального окна
const modal = document.getElementById("createCategoryModal");
const btn = document.getElementById("createCategoryBtn");
const span = document.getElementById("closeModal");
// Когда пользователь кликает на кнопку, открываем модальное окно
btn.onclick = function() {
    modal.style.display = "block";
  }
  // Когда пользователь кликает на <span> (x), закрываем модальное окно
span.onclick = function() {
    modal.style.display = "none";
  }
  // Когда пользователь кликает в любом месте вне модального окна, закрываем его
window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  }
  // Обработчик формы для отправки через AJAX
document.addEventListener("DOMContentLoaded", function() {
  const modal = document.getElementById("createCategoryModal");
  const categoryForm = document.getElementById("categoryForm");
  // Привязываем обработчик отправки формы
  categoryForm.addEventListener("submit", function(event) {
    event.preventDefault(); // Останавливаем стандартное поведение формы
    const formData = new FormData(categoryForm);
    // Проверка: отправка только в случае правильной формы
    fetch("{% url 'create_category' %}", {
        method: "POST",
        body: formData,
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Закрытие модального окна и обновление страницы
          modal.style.display = "none";
          window.location.reload();
        } else {
          alert(data.error || "Ошибка при добавлении категории!");
        }
      })
      .catch(error => {
        console.error("Ошибка:", error);
      });
  });
});

function swapDiagrams() {
  const incomeDiagram = document.getElementById("incomeDiagram");
  const expenseDiagram = document.getElementById("expenseDiagram");
  if (incomeDiagram.classList.contains("active")) {
    incomeDiagram.classList.remove("active");
    incomeDiagram.classList.add("hidden");
    expenseDiagram.classList.contains("active")
    expenseDiagram.classList.remove("hidden");
    expenseDiagram.classList.add("active");
  } else {
    expenseDiagram.classList.remove("active");
    expenseDiagram.classList.add("hidden");
    incomeDiagram.classList.remove("hidden");
    incomeDiagram.classList.add("active");
  }
  positionCategories(".diagram.active .categories .category", ".diagrams-container");
}