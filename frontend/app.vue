<script setup lang="ts">
import { format, parseISO } from 'date-fns'

interface FoodTruckEvent {
  date: string
  vendor: string
  location: string
  location_url?: string
  start_time: string
  end_time: string
  description?: string
  extraction_method?: string
}

interface WebData {
  events: FoodTruckEvent[]
  updated: string
  total_events: number
  haiku?: string
  errors?: string[]
}

const { data, pending, error } = useFetch<WebData>('/data.json')

const groupedEvents = computed(() => {
  if (!data.value?.events) return {}
  
  const groups: Record<string, FoodTruckEvent[]> = {}
  
  // Group by date string (YYYY-MM-DD)
  data.value.events.forEach(event => {
    const dateKey = event.date.split('T')[0]
    if (!groups[dateKey]) {
      groups[dateKey] = []
    }
    groups[dateKey].push(event)
  })
  
  // Sort dates
  return Object.keys(groups).sort().reduce((acc, key) => {
    acc[key] = groups[key]
    return acc
  }, {} as Record<string, FoodTruckEvent[]>)
})

const formatDateParts = (dateStr: string) => {
  const date = new Date(dateStr + 'T12:00:00-08:00')
  return {
    dayName: date.toLocaleDateString('en-US', { weekday: 'long' }),
    monthDay: date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
  }
}

const formatUpdatedDate = (isoString: string) => {
  try {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    })
  } catch (e) {
    return ''
  }
}
</script>

<template>
  <div class="bg-surface text-on-surface min-h-screen font-body selection:bg-primary-mint/30">
    <main class="pt-16 pb-24 px-6 md:px-12 max-w-4xl mx-auto min-h-screen">
      <AppHeader :updated-date="data?.updated ? formatUpdatedDate(data.updated) : undefined" />

      <!-- Loading State -->
      <div v-if="pending" class="py-20 text-center">
        <p class="font-label text-sm uppercase tracking-[0.5em] text-primary-mint animate-pulse">Accessing Archive...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="py-20 text-center border-b border-outline/10">
        <p class="font-headline text-2xl font-bold uppercase text-error mb-2">Archive Interrupted</p>
        <p class="font-label text-sm uppercase tracking-widest text-on-surface-variant">System synchronization failed.</p>
      </div>

      <div v-else>
        <FoodTruckHaiku :haiku="data?.haiku" />

        <!-- Content Grid -->
        <div class="space-y-32 mt-20">
          <DaySection 
            v-for="(events, dateKey, idx) in groupedEvents" 
            :key="dateKey"
            :index="idx"
            :day-name="formatDateParts(dateKey).dayName"
            :month-day="formatDateParts(dateKey).monthDay"
          >
            <TruckItem 
              v-for="(event, eIdx) in events" 
              :key="eIdx"
              :name="event.vendor"
              :location="event.location"
              :location-url="event.location_url"
              :time="`${event.start_time} — ${event.end_time}`"
              :description="event.description"
              :is-vision-extracted="event.extraction_method === 'vision'"
            />
          </DaySection>

          <!-- Archive Termination -->
          <div class="pt-24 text-center">
            <div class="h-px w-full bg-gradient-to-r from-transparent via-outline/10 to-transparent mb-8"></div>
            <span class="font-label text-[10px] uppercase tracking-[1.5em] text-primary-mint font-bold">END OF RECORD</span>
          </div>
        </div>

        <!-- Errors Note -->
        <div v-if="data?.errors?.length" class="mt-12 space-y-2 p-6 bg-surface-container-low border border-error/10">
          <p class="font-label text-[9px] uppercase tracking-widest text-error font-bold mb-2">Integrity Warnings:</p>
          <p v-for="(err, idx) in data.errors" :key="idx" class="text-[9px] uppercase tracking-tighter text-on-surface-variant">
            • {{ err }}
          </p>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}

/* Custom scrollbar for a more integrated feel */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #f9fffb;
}
::-webkit-scrollbar-thumb {
  background: #d4e0db;
}
::-webkit-scrollbar-thumb:hover {
  background: #aab4b0;
}
</style>
