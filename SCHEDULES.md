# Plan: Adding an Events Tab to Around the Grounds

This document outlines the strategy for expanding the "Archive-Lite" tracker to include a dedicated "Events" tab alongside the existing "Food Trucks" view.

## 1. Backend Refactor (Python)

### Data Model Evolution
- Rename `FoodTruckEvent` to `BreweryEvent` (or add a `category` field to the existing model).
- **Categories:** `food-truck`, `trivia`, `live-music`, `community`, `pop-up`.
- Add a `category` field to the `FoodTruckEvent` class in `around_the_grounds/models/schedule.py`.

### Parser Updates
- **Chuck's Greenwood:**
    - Currently filters for `event_type == "Food Truck"`.
    - Refactor `_parse_csv_row` to include rows where `event_type == "Event"`.
    - Map "Event" names containing "Trivia" to the `trivia` category.
- **Squarespace (Ravenna & Ridgecrest):**
    - Currently uses `exclude_patterns` to skip non-truck entries.
    - Refactor `SquarespaceEventsParser` to use these patterns for **categorization** instead of exclusion.
    - If a title matches "Trivia", "Knit Nite", or "Run Club", tag it as `community` or `trivia` rather than dropping it.
- **Seattle Food Truck (Broadview):**
    - This API only provides truck bookings. We may need a second URL in the brewery config specifically for "Events" (e.g., their WordPress calendar page).

### Data Generation (`main.py`)
- Update `generate_web_data` to split the `events` list into two distinct arrays in `data.json`:
    ```json
    {
      "truck_events": [...],
      "other_events": [...],
      "updated": "...",
      "haiku": "..."
    }
    ```

## 2. Frontend Refactor (Nuxt)

### State Management
- In `app.vue`, add a `currentTab` ref:
    ```typescript
    const currentTab = ref<'trucks' | 'events'>('trucks')
    ```

### UI Implementation
- **Tab Toggle:** Add a minimalist text-based toggle below the header:
    ```html
    <div class="flex gap-8 mb-12 border-b border-outline/10 pb-4">
      <button @click="currentTab = 'trucks'" :class="currentTab === 'trucks' ? 'text-primary-mint font-bold' : 'text-on-surface-variant'">TRUCKS</button>
      <button @click="currentTab = 'events'" :class="currentTab === 'events' ? 'text-primary font-bold' : 'text-on-surface-variant'">EVENTS</button>
    </div>
    ```
- **Conditional Rendering:** Use a computed property to filter the displayed list based on the active tab.
- **Theming:** Use `primary-mint` (teal) accents for the Trucks tab and `primary` (salmon) accents for the Events tab to distinguish them visually.

## 3. New Data Sources to Investigate
- **Broadview Taphouse:** Check `broadviewtaphouse.com` for a separate events/calendar page.
- **Shoreline CC:** Look for a campus-wide student life or events calendar URL.
- **Hellbent:** The SimCal parser should already be able to see other events in the same calendar grid; we just need to stop skipping `truck_name` matches that aren't trucks.

## 4. Verification Steps
1. Run scraper and verify `data.json` contains both types of events.
2. Verify tab switching in the UI correctly swaps the data without reloading the page.
3. Ensure "AI Extracted" badges still only apply to the relevant food truck entries.
