// REAL Passio GO! data (GSU)

const PASSIO_BASE = "https://passio3.com/gsu";

// Fetch stops
async function fetchStops() {
    const res = await fetch(`${PASSIO_BASE}/stop`);
    return res.json();
}

// Fetch routes
async function fetchRoutes() {
    const res = await fetch(`${PASSIO_BASE}/routes`);
    return res.json();
}

// Fetch route shape
async function fetchRouteShape(routeId) {
    const res = await fetch(`${PASSIO_BASE}/route/${routeId}/shape`);
    return res.json();
}

// Fetch live buses
async function fetchVehicles() {
    const res = await fetch(`${PASSIO_BASE}/vehicles`);
    return res.json();
}

// ===============================
// DRAW FUNCTIONS (map passed in)
// ===============================

// Draw stops
async function drawPassioStops(map) {
    try {
        const stops = await fetchStops();

        stops.forEach(stop => {
            L.circleMarker([stop.lat, stop.lng], {
                radius: 6,
                color: "#000",
                fillColor: "#ffcc00",
                fillOpacity: 1
            }).addTo(map).bindPopup(stop.name);
        });
    } catch (err) {
        console.error("Error loading Passio stops:", err);
    }
}

// Draw routes
async function drawPassioRoutes(map) {
    try {
        const routes = await fetchRoutes();

        routes.forEach(async route => {
            try {
                const shapeData = await fetchRouteShape(route.id);

                L.polyline(shapeData.shape, {
                    color: route.color || "#000",
                    weight: 4,
                    opacity: 0.8
                }).addTo(map).bindPopup(route.name);
            } catch (err) {
                console.error("Error loading route shape:", route.id, err);
            }
        });
    } catch (err) {
        console.error("Error loading Passio routes:", err);
    }
}

// Live buses
let busMarkers = {};

async function drawLiveBuses(map) {
    try {
        const data = await fetchVehicles();
        if (!data || !data.vehicles) return;

        data.vehicles.forEach(bus => {
            const id = bus.id;
            const latlng = [bus.lat, bus.lng];

            if (busMarkers[id]) {
                busMarkers[id].setLatLng(latlng);
            } else {
                busMarkers[id] = L.marker(latlng, {
                    rotationAngle: bus.heading,
                    icon: L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/61/61212.png",
                        iconSize: [32, 32]
                    })
                }).addTo(map).bindPopup(`Bus ${id}`);
            }
        });
    } catch (err) {
        console.error("Error loading Passio vehicles:", err);
    }
}