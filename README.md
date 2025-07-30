# US Measles Cases Time‑Series Map

This project visualizes monthly U.S. measles case counts at the state level using Mapbox GL JS. The data ingestion pipeline is adapted from Meaghan Batchelor's repository (https://github.com/mmcalend/USMeaslesData), which fetches raw county-level data from the Johns Hopkins University Measles Tracking Team. The map is updated daily at 16:00 UTC. A slider and autoplay controls let you explore trends over time, and popups display both current counts and a mini‐chart of the full time series for each state.

## To view this map:
Go to https://mapacarte.github.io/Measles/

## To Reproduce:

### Prerequisites

* A modern web browser (Chrome, Firefox, Edge, Safari)
* A [Mapbox access token](https://account.mapbox.com/access-tokens/) (there is a free option available)

### Installation

1. Clone or download this repository.
2. Place your Mapbox token in `index.html` (replace `YOUR_MAPBOX_TOKEN`):

   ```html
   <script>
     mapboxgl.accessToken = 'YOUR_MAPBOX_TOKEN';
   </script>
   ```
3. Ensure the `data/` folder contains:

   * `USMeaslesCases.csv` — county‐level case counts from JHU, aggregated by script.
   * `us_states.geojson` — GeoJSON of U.S. states with a `ste_name` array (e.g. `["Idaho"]`).
4. Serve the folder over a local web server (e.g. `npx http-server`, `python -m http.server`, or via your IDE).

### Usage

* Open `http://localhost:8080` (or your chosen port) in your browser.
* Move the date slider or click **Play** to animate monthly case counts.
* Click on a state to view a popup with:

  * The state name
  * The current month’s case count
  * An inline sparkline showing cases over all months

## Customization

* **Color Palette**: Modify the `fill-color` stops in `map.addLayer({ paint: { 'fill-color': [...] } })` to adjust thresholds or hues.
* **Slider Pace**: Change the `pace` constant (milliseconds) in `map.on('load', …)`.
* **Legend**: Edit `addLegend()` in `map.js` to adjust break labels and colors.

## Contributing

Contributions are welcome! To suggest improvements or fixes:

1. Fork this repo and create a new branch (`git checkout -b feature-name`).
2. Commit your changes (`git commit -m 'Add feature'`).
3. Push to your fork (`git push origin feature-name`).
4. Open a Pull Request describing your changes.

## License

This project is released under the [MIT License](LICENSE).


