#pragma once
#include <Arduino.h>

const char DASHBOARD_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>ESP8266 Line Follower Diagnostics</title>
    <style>
        :root { --bg: #121212; --panel: #1e1e1e; --text: #ffffff; --accent: #00e5ff; --danger: #ff1744; --success: #00e676; }
        body { margin: 0; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: var(--text); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--panel); padding-bottom: 10px; margin-bottom: 20px; }
        .badge { padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.9em; }
        .badge.disconnected { background: var(--danger); }
        .badge.connected { background: var(--success); color: black; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--panel); padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h2 { margin-top: 0; color: var(--accent); font-size: 1.2em; border-bottom: 1px solid #333; padding-bottom: 10px; }
        
        /* Motor Controls */
        .slider-container { margin: 15px 0; }
        .slider-container label { display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 5px; }
        input[type=range] { width: 100%; height: 8px; background: #333; border-radius: 5px; outline: none; -webkit-appearance: none; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 20px; height: 20px; border-radius: 50%; background: var(--accent); cursor: pointer; }
        .btn-group { display: flex; gap: 10px; margin-top: 15px; }
        button { flex: 1; padding: 15px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; text-transform: uppercase; transition: opacity 0.2s; }
        button:active { opacity: 0.7; }
        .btn-stop { background: var(--danger); color: white; }
        .btn-dir { background: #333; color: white; border: 1px solid #555; }
        .btn-dir:active { background: var(--accent); color: black; }

        /* Console */
        .console { height: 200px; background: #000; padding: 10px; overflow-y: auto; font-family: monospace; font-size: 0.9em; border-radius: 5px; border: 1px solid #333; }
        .log-msg { margin: 2px 0; }
        .log-err { color: var(--danger); }
        .log-sys { color: var(--accent); }
    </style>
</head>
<body>
    <div class="header">
        <h1>LFR Two-Node Dashboard</h1>
        <div id="status-badge" class="badge disconnected">Disconnected</div>
    </div>
    
    <div class="grid">
        <div class="card">
            <h2>Motor Control & PWM</h2>
            
            <!-- Master Safety and Override Toggles -->
            <div style="display: flex; gap: 15px; margin-bottom: 20px; justify-content: space-between;">
                <div style="flex: 1;">
                    <button id="btn-arm" onclick="toggleArm()" style="width: 100%; padding: 12px; background: var(--danger); color: white; font-weight: bold; border-radius: 5px; border: none; text-transform: uppercase;">DISARMED</button>
                </div>
                <div style="flex: 1;">
                    <button id="btn-mode" onclick="toggleMode()" style="width: 100%; padding: 12px; background: var(--accent); color: black; font-weight: bold; border-radius: 5px; border: none; text-transform: uppercase;">AUTO</button>
                </div>
            </div>

            <div class="slider-container">
                <label><span>Left Motor (M1)</span> <span id="val-left">0</span></label>
                <input type="range" id="slider-left" min="-255" max="255" value="0">
            </div>
            <div class="slider-container">
                <label><span>Right Motor (M2)</span> <span id="val-right">0</span></label>
                <input type="range" id="slider-right" min="-255" max="255" value="0">
            </div>
            
            <div id="joystick-zone" style="width: 200px; height: 200px; background: #333; border-radius: 50%; position: relative; margin: 20px auto; touch-action: none; box-shadow: inset 0 0 10px rgba(0,0,0,0.8);">
                <div id="joystick-thumb" style="width: 60px; height: 60px; background: var(--accent); border-radius: 50%; position: absolute; top: 70px; left: 70px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.5);"></div>
            </div>
            <div class="btn-group">
                <button class="btn-stop" onclick="drive(0,0)">EMERGENCY STOP (SPACE)</button>
            </div>
        </div>
        
        <div class="card" style="grid-column: 1 / -1;">
            <h2>Live Telemetry Console</h2>
            <div class="console" id="console"></div>
        </div>
    </div>

    <script>
        let ws;
        let lastWatchdogState = true;
        let armed = false;
        let modeAuto = true;

        const badge = document.getElementById('status-badge');
        const cons = document.getElementById('console');
        const sliderL = document.getElementById('slider-left');
        const sliderR = document.getElementById('slider-right');
        const valL = document.getElementById('val-left');
        const valR = document.getElementById('val-right');
        
        function log(msg, type='sys') {
            const div = document.createElement('div');
            div.className = 'log-msg log-' + type;
            div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            cons.appendChild(div);
            cons.scrollTop = cons.scrollHeight;
        }

        function connect() {
            ws = new WebSocket('ws://' + window.location.hostname + '/ws');
            ws.onopen = () => {
                badge.className = 'badge connected';
                badge.textContent = 'Connected';
                log('WebSocket connected to ESP8266');
            };
            ws.onclose = () => {
                badge.className = 'badge disconnected';
                badge.textContent = 'Disconnected';
                log('WebSocket disconnected. Reconnecting...', 'err');
                setTimeout(connect, 2000);
            };
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.type === 'telemetry') {
                    if (!data.watchdog_ok && lastWatchdogState) {
                        log('WATCHDOG TIMEOUT / EMERGENCY BRAKE', 'err');
                    }
                    if (data.watchdog_ok && !lastWatchdogState) {
                        log('Watchdog Reset. Motors Ready.', 'sys');
                    }
                    lastWatchdogState = data.watchdog_ok;

                    // Sync Arm state from ESP
                    if (data.armed !== undefined && data.armed !== armed) {
                        armed = data.armed;
                        updateArmUI();
                    }

                    // Sync Control Mode from ESP
                    if (data.mode !== undefined) {
                        const isAuto = (data.mode === 'auto');
                        if (isAuto !== modeAuto) {
                            modeAuto = isAuto;
                            updateModeUI();
                        }
                    }
                }
            };
        }

        function sendMotor(left, right) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'motor', left: left, right: right}));
            }
        }

        function drive(left, right) {
            sliderL.value = left;
            sliderR.value = right;
            valL.textContent = left;
            valR.textContent = right;
            sendMotor(left, right);
        }

        function toggleArm() {
            armed = !armed;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'arm', value: armed}));
            }
            updateArmUI();
        }

        function toggleMode() {
            modeAuto = !modeAuto;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'mode', value: modeAuto ? 'auto' : 'manual'}));
            }
            updateModeUI();
        }

        function updateArmUI() {
            const btn = document.getElementById('btn-arm');
            if (armed) {
                btn.textContent = 'ARMED';
                btn.style.background = 'var(--success)';
                btn.style.color = 'black';
            } else {
                btn.textContent = 'DISARMED';
                btn.style.background = 'var(--danger)';
                btn.style.color = 'white';
            }
        }

        function updateModeUI() {
            const btn = document.getElementById('btn-mode');
            const joyZone = document.getElementById('joystick-zone');
            if (modeAuto) {
                btn.textContent = 'AUTO';
                btn.style.background = 'var(--accent)';
                btn.style.color = 'black';
                joyZone.style.opacity = '0.4';
                joyZone.style.pointerEvents = 'none';
                sliderL.disabled = true;
                sliderR.disabled = true;
            } else {
                btn.textContent = 'MANUAL';
                btn.style.background = '#e0e0e0';
                btn.style.color = 'black';
                joyZone.style.opacity = '1.0';
                joyZone.style.pointerEvents = 'auto';
                sliderL.disabled = false;
                sliderR.disabled = false;
            }
        }

        // Sliders
        sliderL.oninput = () => { valL.textContent = sliderL.value; sendMotor(parseInt(sliderL.value), parseInt(sliderR.value)); };
        sliderR.oninput = () => { valR.textContent = sliderR.value; sendMotor(parseInt(sliderL.value), parseInt(sliderR.value)); };

        // Keyboard support
        window.addEventListener('keydown', (e) => {
            if (e.repeat) return;
            if (modeAuto) return; // Keyboard disabled in Auto mode
            if (e.code === 'ArrowUp' || e.code === 'KeyW') drive(180, 180);
            if (e.code === 'ArrowDown' || e.code === 'KeyS') drive(-180, -180);
            if (e.code === 'ArrowLeft' || e.code === 'KeyA') drive(-150, 150);
            if (e.code === 'ArrowRight' || e.code === 'KeyD') drive(150, -150);
            if (e.code === 'Space') drive(0, 0);
        });
        window.addEventListener('keyup', (e) => {
            if (modeAuto) return;
            if (['ArrowUp','KeyW','ArrowDown','KeyS','ArrowLeft','KeyA','ArrowRight','KeyD'].includes(e.code)) {
                drive(0,0);
            }
        });

        // Joystick
        const zone = document.getElementById('joystick-zone');
        const thumb = document.getElementById('joystick-thumb');
        let jActive = false;
        const maxR = 70;
        let lastSend = 0;
        
        function jStart(e) { if (modeAuto) return; jActive = true; jMove(e); }
        function jEnd(e) { 
            if (!jActive) return;
            jActive = false; 
            thumb.style.transform = `translate(0px, 0px)`; 
            drive(0, 0); 
        }
        function jMove(e) {
            if (!jActive) return;
            e.preventDefault();
            let cx = e.clientX, cy = e.clientY;
            if (e.touches && e.touches.length > 0) {
                cx = e.touches[0].clientX; cy = e.touches[0].clientY;
            }
            const rect = zone.getBoundingClientRect();
            let dx = cx - (rect.left + 100);
            let dy = cy - (rect.top + 100);
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist > maxR) { dx = (dx/dist)*maxR; dy = (dy/dist)*maxR; }
            thumb.style.transform = `translate(${dx}px, ${dy}px)`;
            
            let fwd = -dy / maxR;
            let trn = dx / maxR;
            let l = fwd - trn;
            let r = fwd + trn;
            let m = Math.max(Math.abs(l), Math.abs(r));
            if (m > 1) { l /= m; r /= m; }
            
            let pwm_l = Math.round(l * 255);
            let pwm_r = Math.round(r * 255);
            
            let now = Date.now();
            if (now - lastSend > 50) {
                drive(pwm_l, pwm_r);
                lastSend = now;
            }
        }
        
        zone.addEventListener('mousedown', jStart);
        document.addEventListener('mousemove', jMove);
        document.addEventListener('mouseup', jEnd);
        zone.addEventListener('touchstart', jStart, {passive: false});
        document.addEventListener('touchmove', jMove, {passive: false});
        document.addEventListener('touchend', jEnd);

        connect();
    </script>
</body>
</html>
)rawliteral";
