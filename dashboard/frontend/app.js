let map;
let marker;
let socket;
let pollTimer;
let lastStatus = "NO_DATA";
const DEFAULT_COORDS = [18.5204, 73.8567];
const POLL_INTERVAL_MS = 3000;

function setConnectionState(text, state = "offline") {
    const dot = document.getElementById("connection-dot");
    const label = document.getElementById("connection-text");
    if (!dot || !label) return;

    dot.classList.remove("connected", "polling");
    if (state === "connected") {
        dot.classList.add("connected");
    } else if (state === "polling") {
        dot.classList.add("polling");
    }
    label.textContent = text;
}

function formatMetricValue(value, digits = 3) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric.toFixed(digits) : "--";
}

function formatTimestamp(value) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }

    const parseValue = typeof value === "string" && /^\d+$/.test(value.trim())
        ? Number(value)
        : value;
    const numeric = Number(parseValue);
    let date;

    if (Number.isFinite(numeric) && String(parseValue).trim() !== "") {
        if (numeric > 0 && numeric < 946684800) {
            return `${numeric}s uptime`;
        }
        const epochMs = numeric < 1_000_000_000_000 ? numeric * 1000 : numeric;
        date = new Date(epochMs);
    } else {
        date = new Date(value);
    }

    if (!Number.isNaN(date.getTime())) {
        return date.toLocaleString([], {
            hour12: false,
            month: "short",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    }

    return String(value);
}

function initMap() {
    const mapNode = document.getElementById("map");
    if (!mapNode) return;

    if (!window.L) {
        mapNode.classList.add("map-fallback");
        mapNode.innerHTML = "<p>Map preview unavailable in this browser session. Live coordinates are still updating below.</p>";
        return;
    }

    map = L.map("map").setView(DEFAULT_COORDS, 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    marker = L.marker(DEFAULT_COORDS).addTo(map);
}

function updateStatus(data) {
    if (!data) return;

    const badge = document.getElementById("status-badge");
    const status = (data.status || "NO_DATA").toUpperCase();
    const summary = document.getElementById("status-summary");
    const timestampLabel = formatTimestamp(data.timestamp ?? data.received_at);
    const lastUpdate = document.getElementById("last-update-value");
    const badgeClass = {
        NORMAL: "normal",
        DROWSY: "drowsy",
        YAWN: "yawn",
        YAWNING: "yawn",
        NO_FACE: "no-face",
        NO_DATA: "no-data",
    }[status] || "no-data";

    if (badge) {
        badge.className = `status-badge ${badgeClass}`;
        badge.textContent = status.replace(/_/g, " ");
    }
    if (summary) {
        summary.textContent = {
            NORMAL: "Eyes open and mouth within the normal range.",
            DROWSY: "Eyes remained below the configured EAR threshold.",
            YAWN: "Mouth opening exceeded the configured MAR threshold.",
            YAWNING: "Mouth opening exceeded the configured MAR threshold.",
            NO_FACE: "Camera feed is live but no face is currently tracked.",
            NO_DATA: "Waiting for telemetry from the detector and controller.",
        }[status] || "Waiting for telemetry from the detector and controller.";
    }

    document.getElementById("ear-value").textContent =
        formatMetricValue(data.ear);
    document.getElementById("mar-value").textContent =
        formatMetricValue(data.mar);
    document.getElementById("timestamp-value").textContent = timestampLabel;
    if (lastUpdate) {
        lastUpdate.textContent = timestampLabel;
    }

    const lat = Number(data.lat ?? data.latitude);
    const lon = Number(data.lon ?? data.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
        document.getElementById("lat-value").textContent = lat.toFixed(5);
        document.getElementById("lon-value").textContent = lon.toFixed(5);
        if (map) {
            map.setView([lat, lon], 15);
            marker?.setLatLng([lat, lon]);
        }
    }

    if (status === "DROWSY" || status === "YAWN" || status === "YAWNING") {
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
            <td>${formatTimestamp(alert.timestamp)}</td>
            <td><span class="alert-tag ${(alert.event_type || "").toLowerCase()}">${alert.event_type}</span></td>
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
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Driver Alert", {
            body: `Driver is ${status}!`,
        });
    }
}

async function initCameraFeed() {
    const feed = document.getElementById("camera-feed");
    const statusLabel = document.getElementById("camera-feed-status");
    const sourceLabel = document.getElementById("camera-source");
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
            if (sourceLabel) {
                sourceLabel.textContent = "Source unavailable";
            }
            setStatus(camera.message || "Camera preview unavailable.", true);
            return;
        }

        const streamUrl = camera.url;
        if (sourceLabel) {
            sourceLabel.textContent = `Source: ${String(camera.source || "camera").toUpperCase()}`;
        }
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
        if (sourceLabel) {
            sourceLabel.textContent = "Source unavailable";
        }
        setStatus("Failed to load camera settings.", true);
    }
}

async function refreshDashboard() {
    try {
        const [latestRes, alertsRes, statsRes] = await Promise.all([
            fetch("/latest"),
            fetch("/alerts?limit=20"),
            fetch("/stats"),
        ]);

        const latest = await latestRes.json();
        const alerts = await alertsRes.json();
        const stats = await statsRes.json();

        updateStatus(latest);
        updateAlerts(alerts);
        updateStats(stats);
    } catch (e) {
        console.error("Failed to refresh dashboard:", e);
        setConnectionState("Backend unavailable", "offline");
    }
}

function initSocket() {
    if (!window.io) {
        setConnectionState("Live via polling", "polling");
        return;
    }

    socket = io();

    socket.on("connect", () => {
        setConnectionState("Live via websocket", "connected");
    });

    socket.on("disconnect", () => {
        setConnectionState("Websocket disconnected, polling active", "polling");
    });

    socket.on("driver_update", (data) => {
        updateStatus(data);
        refreshDashboard();
    });
}

function startPolling() {
    refreshDashboard();
    if (pollTimer) {
        clearInterval(pollTimer);
    }
    pollTimer = setInterval(refreshDashboard, POLL_INTERVAL_MS);
}

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initSocket();
    initCameraFeed();
    startPolling();

    const clearButton = document.getElementById("clear-btn");
    if (clearButton) {
        clearButton.addEventListener("click", async () => {
            if (confirm("Clear all driver data and alerts?")) {
                await fetch("/clear", { method: "POST" });
                refreshDashboard();
            }
        });
    }

    if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
    }
});
