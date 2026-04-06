let map;
let marker;
let socket;
let lastStatus = "ALERT";

function initMap() {
    map = L.map("map").setView([18.5204, 73.8567], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    marker = L.marker([18.5204, 73.8567]).addTo(map);
}

function updateStatus(data) {
    if (!data || !data.status) return;

    const badge = document.getElementById("status-badge");
    const status = data.status;

    badge.className = "status-badge " + status.toLowerCase();
    badge.textContent = status;

    document.getElementById("ear-value").textContent = data.ear || "--";
    document.getElementById("mar-value").textContent = data.mar || "--";
    document.getElementById("timestamp-value").textContent = data.timestamp
        ? data.timestamp.split("T")[1].split(".")[0]
        : "--";

    if (data.lat && data.lon) {
        document.getElementById("lat-value").textContent = data.lat;
        document.getElementById("lon-value").textContent = data.lon;
        if (map) {
            map.setView([data.lat, data.lon], 15);
            marker.setLatLng([data.lat, data.lon]);
        }
    }

    if (status === "DROWSY" || status === "YAWNING") {
        if (lastStatus !== status) {
            showNotification(status);
        }
    }
    lastStatus = status;
}

function updateAlerts(alerts) {
    const tbody = document.getElementById("alerts-body");
    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2">No alerts yet</td></tr>';
        return;
    }

    tbody.innerHTML = alerts
        .map(
            (alert) => `
        <tr>
            <td>${alert.timestamp}</td>
            <td><span class="alert-tag ${alert.event_type.toLowerCase()}">${alert.event_type}</span></td>
        </tr>
    `
        )
        .join("");

    const style = document.createElement("style");
    style.textContent = `
        .alert-tag {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .alert-tag.drowsy {
            background: rgba(255,68,68,0.2);
            color: #ff4444;
        }
        .alert-tag.yawning {
            background: rgba(255,165,0,0.2);
            color: #ffa500;
        }
    `;
    document.head.appendChild(style);
}

function updateStats(stats) {
    if (!stats) return;
    document.getElementById("total-records").textContent =
        stats.total_records || 0;
    document.getElementById("drowsy-count").textContent =
        stats.drowsy_alerts || 0;
    document.getElementById("yawn-count").textContent = stats.yawn_alerts || 0;
}

function showNotification(status) {
    if (Notification.permission === "granted") {
        new Notification("Driver Alert", {
            body: `Driver is ${status}!`,
            icon: "/favicon.ico",
        });
    }
}

async function loadInitialData() {
    try {
        const latestRes = await fetch("/latest");
        const latest = await latestRes.json();
        updateStatus(latest);

        const alertsRes = await fetch("/alerts?limit=20");
        const alerts = await alertsRes.json();
        updateAlerts(alerts);

        const statsRes = await fetch("/stats");
        const stats = await statsRes.json();
        updateStats(stats);
    } catch (e) {
        console.error("Failed to load initial data:", e);
    }
}

function initSocket() {
    socket = io();

    socket.on("connect", () => {
        document.getElementById("connection-dot").classList.add("connected");
        document.getElementById("connection-text").textContent = "Connected";
    });

    socket.on("disconnect", () => {
        document.getElementById("connection-dot").classList.remove("connected");
        document.getElementById("connection-text").textContent = "Disconnected";
    });

    socket.on("driver_update", (data) => {
        updateStatus(data);
        fetch("/stats")
            .then((res) => res.json())
            .then(updateStats);
        fetch("/alerts?limit=20")
            .then((res) => res.json())
            .then(updateAlerts);
    });
}

document.getElementById("clear-btn").addEventListener("click", async () => {
    if (confirm("Clear all driver data and alerts?")) {
        await fetch("/clear", { method: "POST" });
        updateStats({ total_records: 0, drowsy_alerts: 0, yawn_alerts: 0 });
        updateAlerts([]);
    }
});

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initSocket();
    loadInitialData();

    if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
    }
});
