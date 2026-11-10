<script setup>
import { ref, onMounted, nextTick } from 'vue'

const zoekterm = ref('')
const categorie = ref('')
const categorieen = ref([])
const statistieken = ref(null)
const foutmelding = ref('')
const laden = ref(false)
const zoekDuur = ref(null) 
const isDarkMode = ref(false)

// Title head is the page title, the text on the tab itself!
useHead({
  title: 'Dealsfinder.nl – Waar ben je naar op zoek?'
})

// Minimumprijs (filtert goedkope advertenties weg)
const minPrijs = ref('')

// Kilometerstand variabelen
const minKm = ref(0)
const maxKm = ref(300000)

onMounted(async () => {
  if (import.meta.client) {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      isDarkMode.value = true
      document.body.classList.add('dark-theme')
    }
  }
  
  try {
    const response = await $fetch('/api/categorieen')
    categorieen.value = response.categorieen
  } catch (error) {
    console.error('Kon categorieën niet ophalen:', error)
  }
})

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.body.classList.add('dark-theme')
    localStorage.setItem('theme', 'dark')
  } else {
    document.body.classList.remove('dark-theme')
    localStorage.setItem('theme', 'light')
  }
}

const formatPrice = (waarde) => {
  const getal = Number(waarde);
  if (isNaN(getal)) return waarde;
  return getal.toLocaleString('nl-NL', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

const formatKm = (waarde) => {
  return Number(waarde).toLocaleString('nl-NL');
}

const formatDuur = (ms) => {        // <-- NEW, directly below formatKm, calculates time between search and results 
  if (ms === null) return ''
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(2).replace('.', ',')} s`
}

function resetZoek() {
  zoekterm.value = ''
  categorie.value = ''
  minPrijs.value = ''
  minKm.value = 0
  maxKm.value = 300000
  statistieken.value = null
  foutmelding.value = ''
  zoekDuur.value = null
}

async function zoekProduct() {
  foutmelding.value = ''
  statistieken.value = null
  zoekDuur.value = null

  if (!zoekterm.value) {
    return
  }

  laden.value = true
  const start = performance.now()   // <-- NEW
  try {
    let url = `/api/stats?term=${encodeURIComponent(zoekterm.value)}`
    if (categorie.value) {
      url += `&categorie=${encodeURIComponent(categorie.value)}`
      if (categorie.value === "Auto's") {
        url += `&min_km=${Number(minKm.value)}&max_km=${Number(maxKm.value)}`
      }
    }
    if (Number(minPrijs.value) > 0) {
      url += `&min_prijs=${Number(minPrijs.value)}`
    }

    const response = await $fetch(url)

    if (response.error) {
      foutmelding.value = response.error
    } else {
      statistieken.value = response
      // NEW: wait until the prices are actually painted
      await nextTick()
      await new Promise(requestAnimationFrame)
      zoekDuur.value = performance.now() - start
    }
  } catch (error) {
    foutmelding.value = "Kan de backend server niet bereiken. Draait FastAPI?"
  } finally {
    laden.value = false
  }
}
</script>

<template>
  <main class="app-container">
    <header class="header">
      <button @click="toggleTheme" class="theme-toggle" aria-label="Wissel thema">
        💡
      </button>

      <img src="/Gemini_Generated_Image_8blk9m8blk9m8blk-Photoroom.png" alt="Dealsfinder Logo" class="Logo" />

      <span class="pill"><span class="pill-dot"></span>Welkom bij dealsfinder.nl!</span>
    </header>

    <!-- INTRO / Wat doet het? -->
    <section class="intro">
      <div class="header-text">
        <span class="sub-heading">Wat is</span>
        <h1 class="gradient-text">Dealsfinder.nl?</h1>
      </div>
    </section>

    <div class="answer-card">
      <div class="answer-meta">
        <span class="answer-label">KORT ANTWOORD</span>
        <span class="answer-dot"></span>
      </div>
      <p class="answer-text">
        <strong>Dealsfinder.nl</strong> is dé slimme tool die Marktplaats 24/7 monitort en je in real-time voorziet van actuele prijsinformatie. Op het grootste tweedehands platform van Nederland. 
        Dealsfinder vergemakkelijkt je zoektocht door al deze gesponsorde ruis direct weg te filteren. Binnen enkele seconden krijg je een heldere, on-demand prijsanalyse op je scherm. Zo bespaar je tijd en geld.
      </p>
    </div>
      <p class="body-text">
        Marktplaats telt meer dan 8 miljoen actieve advertenties en is daarmee het
        drukste tweedehands plein van Nederland. Maar juist dat enorme volume maakt
        het kansloos om handmatig, zelf, de scherpste deals als eerste te zien. Zeker bij
        gewilde elektronica en e-bikes is dit het geval. 
	Dealsfinder probeert deze transactiekosten te verminderen en het overzicht in prijzen terug te brengen.  
      </p>

      <p class="body-text">
        Op Marktplaats komen elke minuut tientallen nieuwe advertenties online. Wie
        de beste prijzen wil scoren - voor een iPhone, een Gazelle ebike, tweedehands bmw's 
        of welk ander populair item dan ook - moet snel reageren. Daarnaast raken vele gebruikers door de talloze advertenties het overzicht kwijt. Vandaar dat een
        Scanner niet langer een "nice to have" product is,  maar misschien wel de standaard voor
        wie serieus tweedehands shopt. Daarnaast is Dealsfinder.nl ook perfect geschikt voor de verkoper die graag snel een inzicht wil hebben in 
	de marktprijs van een product die hij/zij wil verkopen. 
      </p>

    <div class="search-card">
      <div class="input-group">
        <input
          v-model="zoekterm"
          @keyup.enter="zoekProduct"
          type="text"
          placeholder="Wat zoek je? (bijv. Vanmoof s6)"
          class="modern-input"
        />
      </div>

      <div class="category-group">
        <label for="category-select">Categorie (optioneel):</label>
        <select
          id="category-select"
          v-model="categorie"
          class="modern-select">
          <option value="">Alle categorieën</option>
          <option v-for="c in categorieen" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div class="price-group">
        <label for="min-price">Minimumprijs in € (optioneel):</label>
        <input
          id="min-price"
          v-model="minPrijs"
          @keyup.enter="zoekProduct"
          type="number"
          min="0"
          step="1"
          inputmode="numeric"
          placeholder="Bijv. 50 om goedkope advertenties te negeren"
          class="modern-input full-input"
        />
      </div>

      <Transition name="fade">
        <div v-if="categorie === 'Auto\'s'" class="km-group">
          <div class="slider-container">
            <div class="slider-label">
              <span>Minimale kilometerstand</span>
              <strong>{{ formatKm(minKm) }} km</strong>
            </div>
            <input type="range" v-model="minKm" min="0" max="500000" step="5000" class="modern-slider" />
          </div>
          
          <div class="slider-container">
            <div class="slider-label">
              <span>Maximale kilometerstand</span>
              <strong>{{ formatKm(maxKm) }} km</strong>
            </div>
            <input type="range" v-model="maxKm" min="0" max="500000" step="5000" class="modern-slider" />
          </div>
        </div>
      </Transition>

      <button
        @click="zoekProduct"
        :disabled="laden"
        class="modern-button full-width-btn">
        {{ laden ? 'Zoeken...' : 'Zoek' }}
      </button>
    </div>

    <Transition name="fade">
      <div v-if="foutmelding" class="alert alert-error">
        {{ foutmelding }}
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="laden" class="loading-state">
        <button type="button" class="inline-flex items-center text-body bg-neutral-primary-soft border border-default hover:bg-neutral-secondary-medium hover:text-heading focus:ring-4 focus:ring-neutral-tertiary-soft shadow-xs font-medium leading-5 rounded-base text-sm px-4 py-2.5 focus:outline-none" disabled>
          <svg aria-hidden="true" class="w-4 h-4 text-neutral-tertiary animate-spin fill-brand me-2" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
            <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
          </svg>
          Actuele advertenties ophalen...
        </button>
      </div>
    </Transition>  
   
    <Transition name="fade">
      <div v-if="statistieken" class="results-container">
        <div class="results-header">
          <div class="results-title">
            <h2>Resultaten voor "{{ statistieken.term }}"</h2>
            <button @click="resetZoek" class="reset-button" type="button">Reset</button>
          </div>
          <span v-if="statistieken.categorie" class="badge">
            {{ statistieken.categorie }}
          </span>
        </div>

        <div class="stats-grid">
          <div class="stat-wrapper">
            <span class="stat-label">Gemiddelde (€)</span>
            <div class="stat-box primary-box">
              <strong class="stat-value primary-text">{{ formatPrice(statistieken.gemiddelde) }}</strong>
            </div>
          </div>

          <div class="stat-wrapper">
            <span class="stat-label">Mediaan (€)</span>
            <div class="stat-box">
              <strong class="stat-value">{{ formatPrice(statistieken.mediaan) }}</strong>
            </div>
          </div>

          <div class="stat-wrapper">
            <span class="stat-label">Minimum (€)</span>
            <div class="stat-box">
              <strong class="stat-value">{{ formatPrice(statistieken.min_prijs) }}</strong>
            </div>
          </div>

          <div class="stat-wrapper">
            <span class="stat-label">Maximum (€)</span>
            <div class="stat-box">
              <strong class="stat-value">{{ formatPrice(statistieken.max_prijs) }}</strong>
            </div>
          </div>
        </div>

        <div class="stats-footer">
          <div class="footer-item">
            <span class="icon">📊</span> Gebaseerd op <strong>{{ statistieken.aantal }}</strong> advertenties
          </div>
          <div class="footer-item">
            <span class="icon">🎯</span> Prijsbereik (gemiddelde ± deviatie): <strong>{{ statistieken.prijs_range }}</strong>
          </div>
	  <div v-if="zoekDuur !== null" class="footer-item">
	    <span class="icon">⏱️</span> Zoekopdracht duurde <strong>{{ formatDuur(zoekDuur) }}</strong>
            <span v-if="statistieken.server_ms !== undefined">
              (server: {{ formatDuur(statistieken.server_ms) }})
            </span>
	  </div>	
        </div>
      </div>
    </Transition>

  </main>
</template>

<style>
:root {
  /* Wise Theme Colors */
  --color-forest-ink: #163300;
  --color-lime-voltage: #9fe870;
  --color-spruce: #054d28;
  --color-linen-mist: #e2f6d5;
  --color-signal-blue: #0b4c72;
  --color-alarm-red: #cb272f;
  --color-charcoal: #454745;
  --color-obsidian: #0e0f0c;
  --color-pebble: #868685;
  --color-slate: #6a6c6a;
  --color-fog: #e8ebe6;
  --color-paper: #ffffff;

  /* Wise Border Radius & Shadows */
  --radius-lg: 10px;
  --radius-2xl: 16px;
  --radius-3xl: 28.15px;
  --radius-full: 1000px;
  
  --shadow-subtle: rgba(14, 15, 12, 0.12) 0px 0px 0px 1px;
  --shadow-subtle-2: rgb(134, 134, 133) 0px 0px 0px 1px inset;
  --shadow-lg: rgba(0, 0, 0, 0.08) 0px 6px 20px 0px;
}

body {
  background-color: var(--color-fog);
  margin: 0;
  color: var(--color-obsidian);
}

body.dark-theme {
  background-color: var(--color-forest-ink);
  color: var(--color-paper);
}

body.dark-theme .app-container {
  color: var(--color-paper);
}

body.dark-theme .results-header h2,
body.dark-theme .stat-value {
  color: var(--color-paper);
}

body.dark-theme .stat-label,
body.dark-theme .price-group label,
body.dark-theme .category-group label {
  color: var(--color-linen-mist);
}

/* Intro (dark mode) */
body.dark-theme .intro-title,
body.dark-theme .qm,
body.dark-theme .answer-text,
body.dark-theme .body-text,
body.dark-theme .sub-heading {
  color: var(--color-paper);
}

body.dark-theme .answer-card {
  background: var(--color-spruce);
  box-shadow: var(--shadow-subtle);
}

body.dark-theme .pill {
  background: var(--color-spruce);
  color: var(--color-lime-voltage);
  box-shadow: var(--shadow-subtle);
}

body.dark-theme .pill-dot {
  background: var(--color-lime-voltage);
}

body.dark-theme .answer-label {
  color: var(--color-lime-voltage);
}

body.dark-theme .answer-dot {
  background: var(--color-lime-voltage);
}

body.dark-theme .search-card,
body.dark-theme .results-container,
body.dark-theme .stat-box {
  background-color: var(--color-spruce);
  box-shadow: var(--shadow-subtle);
}

body.dark-theme .modern-input,
body.dark-theme .modern-select {
  background-color: var(--color-forest-ink) !important;
  color: var(--color-paper);
  box-shadow: var(--shadow-subtle-2) !important;
}

body.dark-theme .modern-input::placeholder {
  color: var(--color-pebble);
}

body.dark-theme .primary-box {
  background: var(--color-lime-voltage);
  box-shadow: var(--shadow-subtle);
}

body.dark-theme .primary-box .stat-value {
  color: var(--color-forest-ink);
}

body.dark-theme .gradient-text {
  color: var(--color-lime-voltage);
}
</style>

<style scoped>
.app-container {
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
}

.header {
  position: relative;
  text-align: center;
  margin-bottom: 40px;
}

.header-text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.theme-toggle {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 10;
  background: var(--color-paper);
  border: none;
  border-radius: var(--radius-full);
  width: 45px;
  height: 45px;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
  box-shadow: var(--shadow-subtle);
}

.theme-toggle:hover {
  transform: scale(1.05);
}

/* ===== INTRO ===== */
.intro {
  margin: 0 auto 40px;
  text-align: center;
}

.pill {
  display: inline-flex;
  margin-top: 4px;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-full);
  background: var(--color-paper);
  color: var(--color-forest-ink);
  font-size: 14px;
  font-weight: 700;
  box-shadow: var(--shadow-subtle);
}

.pill-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-lime-voltage);
}

.answer-card {
  text-align: left;
  padding: 32px 36px;
  border-radius: var(--radius-3xl);
  background: var(--color-paper);
  box-shadow: var(--shadow-subtle), var(--shadow-lg);
  margin-bottom: 40px;
}

.answer-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  font-size: 12px;
}

.answer-label {
  color: var(--color-charcoal);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.answer-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-lime-voltage);
}

.answer-text {
  margin: 0;
  font-size: 18px;
  line-height: 1.5;
  color: var(--color-obsidian);
}

.answer-text strong {
  font-weight: 700;
}

.body-text {
  text-align: left;
  margin: 0 0 28px;
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-charcoal);
}

/* ===== ZOEKKAART ===== */
.search-card {
  background: var(--color-paper);
  padding: 32px 24px;
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-subtle), var(--shadow-lg);
  margin-bottom: 32px;
  width: 100%;
  box-sizing: border-box;
}

.input-group {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
}

.modern-input, .modern-select {
  flex: 1;
  padding: 16px 20px;
  font-size: 16px;
  border: none;
  border-radius: var(--radius-lg);
  background-color: var(--color-paper) !important;
  color: var(--color-obsidian);
  box-shadow: var(--shadow-subtle-2);
  transition: box-shadow 0.2s ease;
  outline: none;
}

.modern-select {
  width: 100%;
}

.modern-input:focus, .modern-select:focus {
  box-shadow: var(--shadow-subtle-2), 0 0 0 2px var(--color-lime-voltage);
}

.full-width-btn {
  width: 100%;
  margin-top: 24px;
  display: block;
}

.modern-button {
  padding: 16px 28px;
  font-size: 18px;
  font-weight: 700;
  background: var(--color-lime-voltage);
  color: var(--color-forest-ink);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
  box-shadow: var(--shadow-subtle);
}

.modern-button:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.modern-button:active:not(:disabled) {
  transform: translateY(1px);
}

.modern-button:disabled {
  background: var(--color-pebble);
  color: var(--color-fog);
  box-shadow: none;
  cursor: not-allowed;
}

.category-group label, .price-group label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-charcoal);
  margin-bottom: 12px;
}

.price-group {
  margin-top: 20px;
}

.full-input {
  width: 100%;
  box-sizing: border-box;
}

.km-group {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-fog);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.slider-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--color-charcoal);
}

.slider-label strong {
  color: var(--color-obsidian);
  font-weight: 700;
}

.modern-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 8px;
  background: var(--color-fog);
  border-radius: var(--radius-full);
  outline: none;
  box-shadow: var(--shadow-subtle-2);
}

.modern-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-lime-voltage);
  cursor: pointer;
  box-shadow: var(--shadow-subtle);
  transition: transform 0.1s ease;
}

.modern-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 20px;
  color: var(--color-forest-ink);
  font-weight: 700;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 4px solid var(--color-fog);
  border-top-color: var(--color-lime-voltage);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.alert-error {
  background-color: #fce8e8;
  color: var(--color-alarm-red);
  padding: 16px;
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
  font-weight: 700;
  box-shadow: var(--shadow-subtle);
}

.results-container {
  background: var(--color-paper);
  border-radius: var(--radius-3xl);
  padding: 32px;
  box-shadow: var(--shadow-subtle), var(--shadow-lg);
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-fog);
}

.results-title {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.reset-button {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-paper);
  background: var(--color-alarm-red);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.reset-button:hover {
  opacity: 0.9;
}

.results-header h2 {
  margin: 0;
  font-size: 25px;
  color: var(--color-obsidian);
  font-weight: 700;
}

.badge {
  background: var(--color-linen-mist);
  color: var(--color-forest-ink);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 700;
  box-shadow: var(--shadow-subtle);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

.stat-label {
  font-size: 12px;
  color: var(--color-slate);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-box {
  background-color: var(--color-paper);
  padding: 20px 16px;
  border-radius: var(--radius-2xl);
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  box-shadow: var(--shadow-subtle);
  flex-grow: 1;
  min-height: 70px;
}

.stat-value {
  font-size: 25px;
  color: var(--color-obsidian);
  font-weight: 700;
  line-height: 1.1;
}

.primary-box {
  background: var(--color-linen-mist);
}

.primary-text {
  color: var(--color-forest-ink);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-charcoal);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease, transform 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.Logo {
  display: block;
  max-height: 170px;
  max-width: 100%;
  margin: 0 auto 12px;
  object-fit: contain;
}

/* Wise uses stark solid colors rather than vibrant multi-color gradients */
.gradient-text {
  margin: 0;
  font-size: clamp(36px, 8vw, 61px);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.915px;
  color: var(--color-forest-ink);
}

.sub-heading {
  transition: color 0.3s ease; 
  font-size: 36px;
  font-weight: 700;
  color: var(--color-obsidian);
  line-height: 1.1;
  margin-bottom: 8px;
}
</style>
