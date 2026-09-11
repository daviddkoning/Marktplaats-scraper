<script setup>
import { ref, onMounted } from 'vue'

// Variabelen om de invoer en de resultaten op te slaan
const zoekterm = ref('')
const categorie = ref('')          // lege string = "alle categorieën" (geen filter)
const categorieen = ref([])        // lijst met categorienamen, opgehaald bij het laden
const statistieken = ref(null)
const foutmelding = ref('')
const laden = ref(false)  // true zolang de scrape/fetch bezig is

// Categorielijst één keer ophalen zodra de pagina laadt, zodat de
// dropdown-opties altijd exact overeenkomen met wat de backend accepteert
// (scraper_service.py is de enige bron van waarheid voor de lijst).
onMounted(async () => {
  try {
    const response = await $fetch('http://localhost:3000/api/categorieen')
    categorieen.value = response.categorieen
  } catch (error) {
    // Niet fataal -- zoeken zonder categoriefilter blijft gewoon werken
    console.error('Kon categorieën niet ophalen:', error)
  }
})

// De functie die wordt uitgevoerd als je op de knop klikt
async function zoekProduct() {
  foutmelding.value = ''
  statistieken.value = null

  if (!zoekterm.value) {
    return
  }

  laden.value = true
  try {
    // We sturen de zoekterm (bijv. 'fiets') en optioneel de categorie
    // naar onze FastAPI backend
    let url = `http://localhost:3000/api/stats?term=${encodeURIComponent(zoekterm.value)}`
    if (categorie.value) {
      url += `&categorie=${encodeURIComponent(categorie.value)}`
    }
    const response = await $fetch(url)

    if (response.error) {
      foutmelding.value = response.error
    } else {
      statistieken.value = response
    }
  } catch (error) {
    foutmelding.value = "Kan de backend server niet bereiken. Draait FastAPI?"
  } finally {
    // finally, niet in de try/catch losstaand -- zo stopt de spinner
    // ALTIJD, ongeacht of het request slaagt, een error teruggeeft, of
    // een netwerkfout gooit.
    laden.value = false
  }
}
</script>

<template>
  <div style="font-family: 'Droid Sans Mono', sans-serif; padding: 40px; max-width: 600px; margin: auto;">

    <h1>Marktplaats Prijs Analyse</h1>
    <p>Welkom, welk product wil je zoeken? (Wees specifiek)</p>

    <!-- Zoekbalk sectie -->
    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
      <input
        v-model="zoekterm"
        @keyup.enter="zoekProduct"
        type="text"
        placeholder="Zoekterm..."
        style="flex: 1; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <button
        @click="zoekProduct"
        :disabled="laden"
        style="padding: 10px 20px; font-size: 16px; background-color: #0070c9; color: white; border: none; border-radius: 4px; cursor: pointer;">
        {{ laden ? 'Zoeken...' : 'Zoek' }}
      </button>
    </div>

    <!-- Categorie-selectie (optioneel) -->
    <div style="margin-bottom: 20px;">
      <label style="display: block; margin-bottom: 6px; font-size: 14px; color: #555;">
        Categorie (optioneel, voor preciezere resultaten):
      </label>
      <select
        v-model="categorie"
        style="width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px;">
        <option value="">Alle categorieën</option>
        <option v-for="c in categorieen" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <!-- Laadanimatie: getoond zolang de scrape/fetch bezig is -->
    <div v-if="laden" style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; color: #555;">
      <div class="spinner"></div>
      <span>Bezig met scrapen van actuele advertenties, dit kan een paar seconden duren...</span>
    </div>

    <!-- Foutmelding weergave -->
    <div v-if="foutmelding" style="color: red; margin-bottom: 20px;">
      {{ foutmelding }}
    </div>

    <!-- Resultaten weergave (wordt alleen getoond als er succesvolle statistieken zijn) -->
    <div v-if="statistieken" style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #eee;">
      <h2 style="margin-top: 0;">Resultaten voor "{{ statistieken.term }}"</h2>
      <p v-if="statistieken.categorie" style="margin-top: -10px; color: #777; font-size: 14px;">
        Categorie: {{ statistieken.categorie }}
      </p>

      <ul style="list-style-type: none; padding: 0; line-height: 1.8; font-size: 16px;">
        <li><strong>Aantal producten (met prijs):</strong> {{ statistieken.aantal }}</li>
        <li><strong>Minimum prijs:</strong> € {{ statistieken.min_prijs }}</li>
        <li><strong>Maximum prijs:</strong> € {{ statistieken.max_prijs }}</li>
        <hr style="border: 0; height: 1px; background: #ddd; margin: 10px 0;">
        <li><strong>Gemiddelde prijs:</strong> € {{ statistieken.gemiddelde }}</li>
        <li><strong>Mediaan (middelste prijs):</strong> € {{ statistieken.mediaan }}</li>
        <li><strong>Prijs range (gem. ± std.dev.):</strong> {{ statistieken.prijs_range }}</li>
      </ul>
    </div>

  </div>
</template>

<style scoped>
.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #ddd;
  border-top-color: #0070c9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>