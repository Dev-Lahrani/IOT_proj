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

    document.getElementById("ear-value").textContent =
        data.ear ?? "--";
    document.getElementById("mar-value").textContent =
        data.mar ?? "--";
    document.getElementById("timestamp-value").textContent = data.timestamp
        ? (data.timestamp.includes("T")
            ? data.timestamp.split("T")[1].split(".")[0]
            : data.timestamp)
        : "--";

    const lat = Number(data.lat);
    const lon = Number(data.lon);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
        document.getElementById("lat-value").textContent = lat;
        document.getElementById("lon-value").textContent = lon;
        if (map) {
            map.setView([lat, lon], 15);
            marker.setLatLng([lat, lon]);
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

async function initCameraFeed() {
    const feed = document.getElementById("camera-feed");
    const statusLabel = document.getElementById("camera-feed-status");
    if (!feed || !statusLabel) return;

    const setStatus = (text, isError = false) => {
        statusLabel.textContent = text;
        statusLabel.classList.toggle("error", isError);
    };

    const withCacheBust = (url) => {
        const separator = url.includes("?") ? "&" : "?";
        return `${url}${separator}t=${Date.now()}`;
    };

    try {
        const response = await fetch("/camera");
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const camera = await response.json();
        if (!camera.enabled || !camera.url) {
            setStatus(camera.message || "Camera preview unavailable.", true);
            return;
        }

        const streamUrl = camera.url;
        let retryTimer = null;
        feed.onerror = () => {
            setStatus("Camera stream unavailable. Retrying...", true);
            if (retryTimer) {
                clearTimeout(retryTimer);
            }
            retryTimer = setTimeout(() => {
                feed.src = withCacheBust(streamUrl);
            }, 3000);
        };
        feed.onload = () => {
            setStatus(`Live stream connected (${camera.source})`);
        };
        feed.src = withCacheBust(streamUrl);
    } catch (error) {
        console.error("Failed to initialize camera feed:", error);
        setStatus("Failed to load camera settings.", true);
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

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initSocket();
    initCameraFeed();
    loadInitialData();

    const clearButton = document.getElementById("clear-btn");
    if (clearButton) {
        clearButton.addEventListener("click", async () => {
            if (confirm("Clear all driver data and alerts?")) {
                await fetch("/clear", { method: "POST" });
                updateStats({ total_records: 0, drowsy_alerts: 0, yawn_alerts: 0 });
                updateAlerts([]);
            }
        });
    }

    if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
    }
});
