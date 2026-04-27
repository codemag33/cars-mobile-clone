<template>
  <div class="mobile-de-clone">
    <header class="main-header">
      <div class="logo">MOBILE<span>.CLONE</span></div>
      <nav>
        <a href="#" class="active">Легковые</a>
        <a href="#">Мотоциклы</a>
        <a href="#">Грузовики</a>
      </nav>
      <div class="user-menu">👤 Войти</div>
    </header>

    <div class="main-layout">
      <aside class="filters-sidebar">
        <h3>Параметры поиска</h3>

        <div class="filter-group">
          <label>Марка</label>
          <select v-model="filters.brand">
            <option value="">Все марки</option>
            <option v-for="b in uniqueBrands" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Цена до (₽)</label>
          <input v-model.number="filters.maxPrice" type="number" placeholder="Напр. 2000000" />
        </div>

        <div class="filter-group">
          <label>Год от</label>
          <input v-model.number="filters.minYear" type="number" placeholder="2015" />
        </div>

        <div class="filter-group">
          <label>Пробег до (км)</label>
          <input v-model.number="filters.maxMileage" type="number" placeholder="100000" />
        </div>

        <button @click="resetFilters" class="reset-btn">Сбросить всё</button>
        <div class="results-count">Найдено: {{ filteredCars.length }}</div>
      </aside>

      <main class="results-list">
        <div v-if="loading" class="status-msg">Загрузка...</div>
        <div v-else-if="error" class="status-msg error">{{ error }}</div>

        <div v-for="car in filteredCars" :key="car.id" class="listing-card">
          <div class="image-box">
            <img :src="placeholderFor(car)" :alt="`${car.brand} ${car.model}`" />
            <span class="photo-count">📸 12</span>
          </div>

          <div class="details">
            <div class="title-row">
              <h2>{{ car.brand }} {{ car.model }}</h2>
              <span class="price-tag">{{ formatPrice(car.price) }} ₽</span>
            </div>

            <p class="specs">
              <span>📅 {{ car.year }} г.</span>
              <span>🛣️ {{ car.mileage.toLocaleString('ru-RU') }} км</span>
              <span>⛽ {{ car.fuel }}</span>
              <span>⚙️ {{ car.transmission }}</span>
            </p>

            <div class="location">📍 {{ car.location || 'не указано' }}</div>

            <div class="actions">
              <button class="contact-btn">Показать телефон</button>
              <button class="msg-btn">Написать</button>
            </div>
          </div>
        </div>

        <div v-if="!loading && !error && filteredCars.length === 0" class="no-results">
          <p v-if="cars.length === 0">
            Пока нет объявлений. Отправьте Excel-файл боту в Telegram, чтобы добавить машины.
          </p>
          <p v-else>Ничего не найдено. Попробуйте смягчить фильтры.</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCars } from './api.js'

const cars = ref([])
const loading = ref(false)
const error = ref(null)

const filters = ref({
  brand: '',
  maxPrice: null,
  minYear: null,
  maxMileage: null,
})

const PLACEHOLDER_IMAGES = {
  BMW: 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=600&q=70',
  Audi: 'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=600&q=70',
  Mercedes: 'https://images.unsplash.com/photo-1617814086367-d4f1d4b85c3a?w=600&q=70',
  Toyota: 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=600&q=70',
  Kia: 'https://images.unsplash.com/photo-1621135802920-133df287f89c?w=600&q=70',
}
const FALLBACK_IMG =
  'https://images.unsplash.com/photo-1502877338535-766e1452684a?w=600&q=70'

function placeholderFor(car) {
  return PLACEHOLDER_IMAGES[car.brand] || FALLBACK_IMG
}

function formatPrice(price) {
  return Number(price).toLocaleString('ru-RU')
}

const uniqueBrands = computed(() => [...new Set(cars.value.map((c) => c.brand))].sort())

const filteredCars = computed(() =>
  cars.value.filter((car) => {
    const brandMatch = !filters.value.brand || car.brand === filters.value.brand
    const priceMatch = !filters.value.maxPrice || car.price <= filters.value.maxPrice
    const yearMatch = !filters.value.minYear || car.year >= filters.value.minYear
    const mileageMatch = !filters.value.maxMileage || car.mileage <= filters.value.maxMileage
    return brandMatch && priceMatch && yearMatch && mileageMatch
  })
)

function resetFilters() {
  filters.value = { brand: '', maxPrice: null, minYear: null, maxMileage: null }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    cars.value = await fetchCars()
  } catch (e) {
    error.value = `Не удалось загрузить объявления: ${e.message}`
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.mobile-de-clone {
  min-height: 100vh;
}

.main-header {
  background: #1a1a1a;
  color: white;
  padding: 15px 50px;
  display: flex;
  align-items: center;
  gap: 40px;
}
.logo {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -1px;
}
.logo span {
  color: #ff5a00;
}
nav {
  display: flex;
  gap: 24px;
}
nav a {
  color: #ccc;
  text-decoration: none;
  font-size: 14px;
  font-weight: bold;
}
nav a:hover,
nav a.active {
  color: white;
}
.user-menu {
  margin-left: auto;
  cursor: pointer;
  font-size: 14px;
}

.main-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  padding: 20px 50px;
  max-width: 1300px;
  margin: 0 auto;
}

.filters-sidebar {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  height: fit-content;
}
.filters-sidebar h3 {
  margin-top: 0;
}
.filter-group {
  margin-bottom: 15px;
}
.filter-group label {
  display: block;
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 5px;
  color: #666;
}
select,
input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.reset-btn {
  width: 100%;
  padding: 10px;
  background: none;
  border: 1px solid #ff5a00;
  color: #ff5a00;
  font-weight: bold;
  cursor: pointer;
  border-radius: 4px;
  margin-top: 10px;
}
.reset-btn:hover {
  background: #ff5a00;
  color: white;
}
.results-count {
  margin-top: 15px;
  font-size: 14px;
  font-weight: bold;
  text-align: center;
  color: #ff5a00;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.status-msg {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}
.status-msg.error {
  color: #c00;
}

.listing-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s;
}
.listing-card:hover {
  transform: scale(1.005);
}

.image-box {
  position: relative;
  width: 260px;
  min-width: 260px;
  background: #eee;
}
.image-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.photo-count {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 6px;
  font-size: 11px;
  border-radius: 3px;
}

.details {
  padding: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
}
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  gap: 12px;
}
.title-row h2 {
  margin: 0;
  font-size: 18px;
  color: #005ea6;
  cursor: pointer;
}
.price-tag {
  font-size: 20px;
  font-weight: 800;
  color: #1a1a1a;
  white-space: nowrap;
}

.specs {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 13px;
  color: #555;
  margin: 0 0 10px;
}
.location {
  color: #888;
  font-size: 12px;
  margin-bottom: 15px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
}
.contact-btn {
  background: #ff5a00;
  color: white;
  border: none;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 4px;
  cursor: pointer;
  flex: 1;
}
.contact-btn:hover {
  background: #e54e00;
}
.msg-btn {
  background: white;
  border: 1px solid #005ea6;
  color: #005ea6;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 4px;
  cursor: pointer;
}
.msg-btn:hover {
  background: #005ea6;
  color: white;
}

.no-results {
  background: white;
  padding: 40px;
  border-radius: 8px;
  text-align: center;
  color: #666;
}

@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
    padding: 20px;
  }
  .listing-card {
    flex-direction: column;
  }
  .image-box {
    width: 100%;
    height: 200px;
    min-width: 0;
  }
  .main-header {
    padding: 15px 20px;
  }
}
</style>
