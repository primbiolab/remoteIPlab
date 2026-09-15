class PendulumApp {
  constructor() {
    this.ws = null;
    this.isRunning = false;
    this.isMonitoring = false;
    this.serialConnected = false;
    this._gainsSynced = false;
    this.drawer = null;
    this.charts = {};

    this.backendUrl = `http://${window.location.hostname}:8080`;
    this.wsUrl = `ws://${window.location.hostname}:8080/ws`;

    
    this.initElements();
    this.initEvents();
    this.initCharts();
    this.checkBackend();
    this.scanPorts();
    setInterval(() => this.checkBackend(), 10000);
    setInterval(() => this.scanPorts(), 5000);
    this.navigate("pendulum"); 
  }

  initElements() {
    this.sidebar = document.getElementById("sidebar");
    this.toggleBtn = document.getElementById("toggleBtn");
    this.navBtns = document.querySelectorAll(".nav-btn[data-page]");
    this.pages = {
      home: document.getElementById("homePage"),
      pendulum: document.getElementById("pendulumPage"),
      graphs: document.getElementById("graphsPage"),
    };

    this.controlType = document.getElementById("controlType");
    this.comPort = document.getElementById("comPort");
    this.baudRate = document.getElementById("baudRate");
    this.scanPortsBtn = document.getElementById("scanPortsBtn");
    this.connectSerialBtn = document.getElementById("connectSerialBtn");
    this.disconnectSerialBtn = document.getElementById("disconnectSerialBtn");
    this.serialStatus = document.getElementById("serialStatus");
    this.monitorBtn = document.getElementById("monitorBtn");
    this.runBtn = document.getElementById("runBtn");
    this.stopBtn = document.getElementById("stopBtn");
    this.connectionStatus = document.getElementById("connectionStatus");

    this.posVal = document.getElementById("posVal");
    this.velVal = document.getElementById("velVal");
    this.angleVal = document.getElementById("angleVal");
    this.angVelVal = document.getElementById("angVelVal");
    this.actionVal = document.getElementById("actionVal");
    this.modeVal = document.getElementById("modeVal");
    this.rawPulsesVal = document.getElementById("rawPulsesVal");
    this.rawAngleVal = document.getElementById("rawAngleVal");
    this.exitBtn = document.getElementById("exitBtn");

    this.calibResetBtn = document.getElementById("calibResetBtn");
    this.calibLeftBtn = document.getElementById("calibLeftBtn");
    this.calibRightBtn = document.getElementById("calibRightBtn");
    this.calibCenterBtn = document.getElementById("calibCenterBtn");
    this.calibMoveCenterBtn = document.getElementById("calibMoveCenterBtn");
    this.calibApplyBtn = document.getElementById("calibApplyBtn");
    this.calibLeftVal = document.getElementById("calibLeftVal");
    this.calibRightVal = document.getElementById("calibRightVal");
    this.calibCenterVal = document.getElementById("calibCenterVal");
    this.calibLimitVal = document.getElementById("calibLimitVal");

    this.clearGraphsBtn = document.getElementById("clearGraphsBtn");
    this.exportCsvBtn = document.getElementById("exportCsvBtn");
    this.pauseGraphs = document.getElementById("pauseGraphs");

    this.applyGainsBtn = document.getElementById("applyGainsBtn");

    this.moveLeftBtn = document.getElementById("moveLeftBtn");
    this.moveRightBtn = document.getElementById("moveRightBtn");
    this.dirVoltage = document.getElementById("dirVoltage");

    this.cameraSelect = document.getElementById("cameraSelect");
    this.toggleCameraBtn = document.getElementById("toggleCameraBtn");
    this.cameraFeed = document.getElementById("cameraFeed");
    this.cameraOff = document.getElementById("cameraOff");
    this.cameraStream = null;

    this.themeToggle = document.getElementById("themeToggle");
    this._applyThemeUI();
  }

  initEvents() {
    this.toggleBtn.addEventListener("click", () => this.sidebar.classList.toggle("collapsed"));

    this.navBtns.forEach((btn) => {
      btn.addEventListener("click", () => this.navigate(btn.dataset.page));
    });

    this.exitBtn.addEventListener("click", () => {
      if (confirm("¿Salir del sistema?")) { this.stopControl(); window.close(); }
    });

    this.monitorBtn.addEventListener("click", () => this.toggleMonitor());
    this.runBtn.addEventListener("click", () => this.startControl());
    this.stopBtn.addEventListener("click", () => this.stopControl());
    
    if (this.calibResetBtn) this.calibResetBtn.addEventListener("click", () => this.resetCalibration());
    if (this.calibLeftBtn) this.calibLeftBtn.addEventListener("click", () => this.setLeftLimit());
    if (this.calibRightBtn) this.calibRightBtn.addEventListener("click", () => this.setRightLimit());
    if (this.calibCenterBtn) this.calibCenterBtn.addEventListener("click", () => this.computeCenter());
    if (this.calibMoveCenterBtn) this.calibMoveCenterBtn.addEventListener("click", () => this.moveToCenter());
    if (this.calibApplyBtn) this.calibApplyBtn.addEventListener("click", () => this.applyCalibration());

    this.scanPortsBtn.addEventListener("click", () => this.scanPorts());
    this.connectSerialBtn.addEventListener("click", () => this.connectSerial());
    this.disconnectSerialBtn.addEventListener("click", () => this.disconnectSerial());

    this.controlType.addEventListener("change", () => {
      this.wsSend({ action: "set_controller", controller: this.controlType.value });
    });

    this.clearGraphsBtn.addEventListener("click", () => this._clearAllCharts());
    this.exportCsvBtn.addEventListener("click", () => this.exportData());

    const applyGains = () => {
      const gains = ["k0", "k1", "k2", "k3"].map((id) => parseFloat(document.getElementById(id).value));
      if (gains.some(isNaN)) return alert("Ganancias inválidas");
      this.wsSend({ action: "set_gains", gains });
      this._showConfirmation("applyGainsToast", "Ganancias enviadas");
    };
    this.applyGainsBtn.addEventListener("click", applyGains);

    // Direction buttons: press & hold
    this.moveLeftBtn.addEventListener("mousedown", (e) => { e.preventDefault(); this.startMoving("left"); });
    this.moveLeftBtn.addEventListener("mouseup", () => this.stopMoving());
    this.moveLeftBtn.addEventListener("mouseleave", () => this.stopMoving());
    this.moveLeftBtn.addEventListener("touchstart", (e) => { e.preventDefault(); this.startMoving("left"); });
    this.moveLeftBtn.addEventListener("touchend", (e) => { e.preventDefault(); this.stopMoving(); });

    this.moveRightBtn.addEventListener("mousedown", (e) => { e.preventDefault(); this.startMoving("right"); });
    this.moveRightBtn.addEventListener("mouseup", () => this.stopMoving());
    this.moveRightBtn.addEventListener("mouseleave", () => this.stopMoving());
    this.moveRightBtn.addEventListener("touchstart", (e) => { e.preventDefault(); this.startMoving("right"); });
    this.moveRightBtn.addEventListener("touchend", (e) => { e.preventDefault(); this.stopMoving(); });

    this.toggleCameraBtn.addEventListener("click", () => this.toggleCamera());
    this.cameraSelect.addEventListener("change", () => this.onCameraChange());

    this.themeToggle.addEventListener("click", () => this.toggleTheme());
  }

  navigate(pageId) {
    Object.values(this.pages).forEach((p) => { if (p) p.classList.add("hidden"); });
    const page = this.pages[pageId];
    if (page) page.classList.remove("hidden");
    this.navBtns.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.page === pageId);
    });
    
    if (pageId === "pendulum") {
      setTimeout(() => {
        const c = document.getElementById("pendulumCanvas");
        if (c) {
          if (!this.drawer) this.drawer = new PendulumDrawer(c);
          else this.drawer.setupCanvas();
          this.drawer.draw({ angle: 0, pos: 0, action: 0 });
        }
        ["pPosChart","pAngleChart","pActionChart","pVelChart"].forEach((id) => {
          const ch = this.charts[id];
          if (ch) { ch.setupCanvas(); ch.draw(); }
        });
        this.listCameras();
      }, 50);
    }
    if (pageId === "graphs") {
      setTimeout(() => {
        ["posChart","angleChart","actionChart","velChart"].forEach((id) => {
          const ch = this.charts[id];
          if (ch) { ch.setupCanvas(); ch.draw(); }
        });
      }, 50);
    }
  }

  _pulsesToCm(pulses) {
    return (2 * Math.PI * pulses / 2400) * 1.2;
  }

  _showConfirmation(toastId, message) {
    const el = document.getElementById(toastId);
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(this._toastTimers?.[toastId]);
    if (!this._toastTimers) this._toastTimers = {};
    this._toastTimers[toastId] = setTimeout(() => el.classList.remove("show"), 2500);
  }

  _defaultPosLimitCm() {
    return this._pulsesToCm(this._defaultPosLimitPulses || 5000);
  }

  initCharts() {
    this._defaultPosLimitPulses = 5000;
    const posLimit = this._defaultPosLimitCm();

    const full = [
      { id: "posChart", cssColor: "--accent", color: "#e0571c", min: -posLimit, max: posLimit },
      { id: "angleChart", cssColor: "--green", color: "#3f9468", min: -180, max: 180 },
      { id: "actionChart", cssColor: "--red", color: "#e0573f", min: -12, max: 12 },
      { id: "velChart", cssColor: "--peach", color: "#e0a020", min: -5, max: 5 },
    ];
    full.forEach((cfg) => {
      const c = document.getElementById(cfg.id);
      if (c) this.charts[cfg.id] = new RealtimeChart(c, { color: cfg.color, cssColor: cfg.cssColor, minY: cfg.min, maxY: cfg.max });
    });

    const compact = [
      { id: "pPosChart", cssColor: "--accent", color: "#e0571c", min: -posLimit, max: posLimit },
      { id: "pAngleChart", cssColor: "--green", color: "#3f9468", min: -180, max: 180 },
      { id: "pActionChart", cssColor: "--red", color: "#e0573f", min: -12, max: 12 },
      { id: "pVelChart", cssColor: "--peach", color: "#e0a020", min: -5, max: 5 },
    ];
    compact.forEach((cfg) => {
      const c = document.getElementById(cfg.id);
      if (c) this.charts[cfg.id] = new RealtimeChart(c, { color: cfg.color, cssColor: cfg.cssColor, minY: cfg.min, maxY: cfg.max, compact: true });
    });
  }

  _clearAllCharts() {
    Object.values(this.charts).forEach((c) => c.clear());
  }

  async checkBackend() {
    try {
      const ac = new AbortController();
      setTimeout(() => ac.abort(), 2000);
      const r = await fetch(`${this.backendUrl}/health`, { signal: ac.signal });
      if (r.ok) {
        const d = await r.json();
        this.setConnected(true, d.connected ? "Serial" : "OK");
        if (d.calibration && d.calibration.calibrated) {
          this.calibrated = true;
          this._defaultPosLimitPulses = d.calibration.limit_pulses;
          const posLimit = this._defaultPosLimitCm();
          ["posChart", "pPosChart"].forEach((id) => {
            const ch = this.charts[id];
            if (ch) { ch.minY = -posLimit; ch.maxY = posLimit; }
          });
          if (this.calibLimitVal && this.calibLimitVal.textContent === "—") {
            this.calibLimitVal.textContent = d.calibration.limit_pulses.toFixed(0);
          }
        } else if (d.calibration) {
          this.calibrated = false;
        }
        if (Array.isArray(d.gains) && d.gains.length === 4 && !this._gainsSynced) {
          this._gainsSynced = true;
          ["k0", "k1", "k2", "k3"].forEach((id, i) => {
            const el = document.getElementById(id);
            if (el) el.value = d.gains[i];
          });
        }
        if (d.monitoring && !this.isMonitoring) {
          this.isMonitoring = true;
          this.monitorBtn.textContent = "⏹ Detener Monitoreo";
          this.monitorBtn.classList.add("active");
          this.monitorBtn.disabled = false;
          this.runBtn.disabled = true;
          if (this.modeVal) this.modeVal.textContent = "Monitor";
          this.connectWs();
        } else if (!d.monitoring && this.isMonitoring && !this.isRunning) {
          this.isMonitoring = false;
          this.monitorBtn.textContent = "🔍 Monitorear";
          this.monitorBtn.classList.remove("active");
          this.runBtn.disabled = false;
        }
      } else this.setConnected(false);
    } catch { this.setConnected(false); }
  }

  setConnected(ok, mode) {
    const dot = this.connectionStatus.querySelector(".status-dot");
    const text = this.connectionStatus.querySelector(".status-text");
    if (ok) { dot.style.background = "var(--green)"; text.textContent = `Conectado — ${mode || "Online"}`; }
    else { dot.style.background = "var(--red)"; text.textContent = "Desconectado"; }
    this.serialConnected = ok && mode === "Serial";
    this._updateMonitorAvailability();
  }

  _updateMonitorAvailability() {
    if (!this.monitorBtn) return;
    let enabled = false;
    if (!this.isRunning && (this.isMonitoring || this.serialConnected)) enabled = true;
    this.monitorBtn.disabled = !enabled;
    this.monitorBtn.title = enabled
      ? ""
      : "Haz clic en Conectar serial (Arduino) para habilitar el monitoreo.";
  }

  async scanPorts() {
    try {
      const r = await fetch(`${this.backendUrl}/ports`);
      const d = await r.json();
      const sel = this.comPort;
      sel.innerHTML = `<option value="/dev/ttyACM0">/dev/ttyACM0 — Predeterminado</option>`;
      const added = new Set(["/dev/ttyACM0"]);
      (d.ports || []).forEach((p) => {
        if (added.has(p.device)) return;
        added.add(p.device);
        const o = document.createElement("option");
        o.value = p.device;
        o.textContent = `${p.device} — ${p.description}`;
        sel.appendChild(o);
      });
      sel.value = "/dev/ttyACM0";
    } catch (e) { console.warn("Port scan:", e); }
  }

  wsSend(cmd) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(cmd));
    } else {
      fetch(`${this.backendUrl}/controller`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ controller: cmd.controller || "LQR", gains: cmd.gains }),
      }).catch(() => {});
    }
  }

  connectWs() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    try {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => {
        console.log("WS connected");
        this.wsSend({ action: "set_controller", controller: this.controlType.value });
      };
      this.ws.onmessage = (e) => {
        try { this.updateUI(JSON.parse(e.data)); }
        catch (err) { /* ignore */ }
      };
      this.ws.onclose = () => { console.log("WS closed"); setTimeout(() => this.connectWs(), 3000); };
      this.ws.onerror = () => { this.ws.close(); };
    } catch (e) { console.error("WS:", e); }
  }

  async toggleMonitor() {
    if (this.isMonitoring) {
      await this.stopMonitor();
    } else {
      await this.startMonitor();
    }
  }

  async startMonitor() {
    if (this.isMonitoring || this.isRunning) return;
    try {
      await fetch(`${this.backendUrl}/monitor/start`, { method: "POST" });
    } catch (e) {
      alert("Error al iniciar monitoreo: " + (e.message || "desconocido"));
      return;
    }
    this.isMonitoring = true;
    this.connectWs();
    this.monitorBtn.textContent = "⏹ Detener Monitoreo";
    this.monitorBtn.classList.add("active");
    this.monitorBtn.disabled = false;
    this.runBtn.disabled = true;
    if (this.modeVal) this.modeVal.textContent = "Monitor";
    const c = document.getElementById("pendulumCanvas");
    if (c && !this.drawer) this.drawer = new PendulumDrawer(c);
  }

  async stopMonitor() {
    this.isMonitoring = false;
    try { await fetch(`${this.backendUrl}/monitor/stop`, { method: "POST" }); } catch {}
    this.monitorBtn.textContent = "🔍 Monitorear";
    this.monitorBtn.classList.remove("active");
    this.monitorBtn.disabled = false;
    this.runBtn.disabled = false;
    if (this.modeVal) this.modeVal.textContent = "Serial";
  }

  async startControl() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      const r = await fetch(`${this.backendUrl}/start`, { method: "POST" });
      if (!r.ok) {
        const d = await r.json();
        this.isRunning = false;
        throw new Error(d.error || `Error ${r.status}`);
      }
    } catch (e) {
      this.isRunning = false;
      alert("Error al iniciar: " + (e.message || "desconocido"));
      return;
    }
    this.connectWs();

    const c = document.getElementById("pendulumCanvas");
    if (c && !this.drawer) this.drawer = new PendulumDrawer(c);

    this.runBtn.disabled = true;
    this.stopBtn.disabled = false;
    this.monitorBtn.disabled = true;
    if (this.modeVal) this.modeVal.textContent = "Serial";
  }

  async stopControl() {
    this.isRunning = false;
    try {
      const r = await fetch(`${this.backendUrl}/stop`, { method: "POST" });
      const d = await r.json();
      if (d.monitor) {
        this.isMonitoring = true;
        this.monitorBtn.textContent = "⏹ Detener Monitoreo";
        this.monitorBtn.classList.add("active");
        this.monitorBtn.disabled = false;
        this.runBtn.disabled = true;
        if (this.modeVal) this.modeVal.textContent = "Monitor";
      }
    } catch {}
    this.stopBtn.disabled = true;
  }

  updateUI(data) {
    if (!data) return;
    this.lastData = data;

    if (data.event === "out_of_limits") {
      if (this.modeVal) this.modeVal.textContent = "RECUPERANDO";
      alert(data.message || "Fuera de limites. Regresando al centro...");
    }

    if (this.drawer) this.drawer.draw(data);
    if (this.posVal) this.posVal.textContent = (data.pos || 0).toFixed(3);
    if (this.velVal) this.velVal.textContent = (data.vel || 0).toFixed(3);
    if (this.angleVal) this.angleVal.textContent = (data.angle || 0).toFixed(1);
    if (this.angVelVal) this.angVelVal.textContent = (data.ang_vel || 0).toFixed(3);
    if (this.actionVal) this.actionVal.textContent = (data.action || 0).toFixed(2);
    if (this.modeVal) this.modeVal.textContent = data.monitor ? "Monitor" : "Serial";
    if (this.rawPulsesVal) this.rawPulsesVal.textContent = data.raw_pulses != null ? data.raw_pulses : "-";
    if (this.rawAngleVal) this.rawAngleVal.textContent = data.raw_angle_deg != null ? data.raw_angle_deg.toFixed(1) : "-";

    if (this.pauseGraphs && this.pauseGraphs.checked) return;

    if (data.pos_limit_pulses != null && data.pos_limit_pulses !== this._lastPosLimitPulses && this.calibrated) {
      this._lastPosLimitPulses = data.pos_limit_pulses;
      const posLimit = this._pulsesToCm(data.pos_limit_pulses);
      ["posChart", "pPosChart"].forEach((id) => {
        const ch = this.charts[id];
        if (ch) { ch.minY = -posLimit; ch.maxY = posLimit; }
      });
    }

    const updates = [
      ["posChart", "pPosChart", data.pos || 0],
      ["angleChart", "pAngleChart", data.angle || 0],
      ["actionChart", "pActionChart", data.action || 0],
      ["velChart", "pVelChart", data.vel || 0],
    ];
    updates.forEach(([fullId, compactId, val]) => {
      if (this.charts[fullId]) { this.charts[fullId].push(val); this.charts[fullId].draw(); }
      if (this.charts[compactId]) { this.charts[compactId].push(val); this.charts[compactId].draw(); }
    });
  }

  async connectSerial() {
    const port = this.comPort.value;
    if (!port) {
      if (this.serialStatus) {
        this.serialStatus.innerHTML = '<span style="color:var(--yellow)">Selecciona un puerto</span>';
      }
      return;
    }
    const baud = parseInt(this.baudRate.value);
    try {
      const r = await fetch(`${this.backendUrl}/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ port, baudrate: baud }),
      });
      const d = await r.json();
      if (!r.ok) {
        if (this.serialStatus) {
          this.serialStatus.innerHTML = `<span style="color:var(--red)">✖ Error: ${d.error || "conexión fallida"}</span>`;
        }
        return;
      }
      if (this.serialStatus) {
        this.serialStatus.innerHTML = `<span style="color:var(--green)">✔ Conectado a ${port} (${baud})</span>`;
      }
      this.checkBackend();
    } catch (e) {
      if (this.serialStatus) {
        this.serialStatus.innerHTML = `<span style="color:var(--red)">✖ Error: conexión fallida — ¿El servidor está corriendo?</span>`;
      }
    }
  }

  async disconnectSerial() {
    try {
      await fetch(`${this.backendUrl}/disconnect`, { method: "POST" });
      if (this.serialStatus) this.serialStatus.textContent = "Desconectado";
      this.checkBackend();
    } catch {}
  }

    async resetCalibration() {
      try {
        await fetch(`${this.backendUrl}/calibrate/reset`, { method: "POST" });
      } catch {}
      this.calibrated = false;
      this.calibLeftVal.textContent = "—";
      this.calibRightVal.textContent = "—";
      this.calibCenterVal.textContent = "—";
      this.calibLimitVal.textContent = "—";
      this.calibApplyBtn.disabled = true;
    }

    async _apiPost(path) {
      const r = await fetch(`${this.backendUrl}${path}`, { method: "POST" });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || `Error ${r.status}`);
      return d;
    }

    async setLeftLimit() {
      try {
        const d = await this._apiPost("/calibrate/left");
        this.calibLeftVal.textContent = d.pulses.toFixed(0);
        if (this.calibRightVal.textContent !== "—") this.calibrated = true;
        this.calibApplyBtn.disabled = true;
      } catch (e) {
        alert("Extremo Izquierdo: " + e.message);
      }
    }

    async setRightLimit() {
      try {
        const d = await this._apiPost("/calibrate/right");
        this.calibRightVal.textContent = d.pulses.toFixed(0);
        if (this.calibLeftVal.textContent !== "—") this.calibrated = true;
        this.calibApplyBtn.disabled = true;
      } catch (e) {
        alert("Extremo Derecho: " + e.message);
      }
    }

    async computeCenter() {
      try {
        const d = await this._apiPost("/calibrate/compute_center");
        this.calibCenterVal.textContent = d.center_pulses.toFixed(0);
        this.calibLeftVal.textContent = d.left_pulses.toFixed(0);
        this.calibRightVal.textContent = d.right_pulses.toFixed(0);
        this.calibLimitVal.textContent = d.limit_pulses.toFixed(0);
        this.calibApplyBtn.disabled = true;
      } catch (e) {
        alert("Calcular Centro: " + e.message);
      }
    }

    async moveToCenter() {
      try {
        await this._apiPost("/calibrate/move_to_center");
        this.calibApplyBtn.disabled = false;
      } catch (e) {
        alert("Mover a Centro: " + e.message);
      }
    }

    async applyCalibration() {
      try {
        const d = await this._apiPost("/calibrate/apply");
        this.calibLimitVal.textContent = d.limit_pulses.toFixed(0);
        this.calibApplyBtn.disabled = true;
        alert(`Calibración aplicada: límite ${d.limit_pulses} pulsos (${d.limit_cm.toFixed(2)} cm)`);
      } catch (e) {
        alert("Aplicar Calibración: " + e.message);
      }
    }

  async exportData() {
    try {
      const r = await fetch(`${this.backendUrl}/data/export`);
      if (!r.ok) throw new Error("Error al exportar");
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pendulum_data_${new Date().toISOString().slice(0,19).replace(/[:-]/g,"")}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Error al exportar datos: " + e.message);
    }
  }

  async startMoving(direction) {
    if (!this.dirVoltage) return;
    const voltage = parseFloat(this.dirVoltage.value) || 5;
    try {
      await fetch(`${this.backendUrl}/move/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ direction, voltage }),
      });
    } catch (e) {
      console.warn("Move error:", e);
    }
  }

  async stopMoving() {
    try {
      await fetch(`${this.backendUrl}/move/stop`, { method: "POST" });
    } catch (e) {
      console.warn("Move stop error:", e);
    }
  }

  async listCameras() {
    try {
      let devices = await navigator.mediaDevices.enumerateDevices();
      let cameras = devices.filter(d => d.kind === "videoinput");

      if (cameras.length === 0 || cameras.every(c => !c.label)) {
        const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
        tempStream.getTracks().forEach(t => t.stop());
        devices = await navigator.mediaDevices.enumerateDevices();
        cameras = devices.filter(d => d.kind === "videoinput");
      }

      this.cameraSelect.innerHTML = "";
      if (cameras.length === 0) {
        this.cameraSelect.innerHTML = '<option value="">No se encontraron cámaras</option>';
        return;
      }
      cameras.forEach((cam, i) => {
        const opt = document.createElement("option");
        opt.value = cam.deviceId;
        opt.textContent = cam.label || `Cámara ${i + 1}`;
        this.cameraSelect.appendChild(opt);
      });
    } catch (e) {
      console.warn("Error listando cámaras:", e);
      this.cameraSelect.innerHTML = '<option value="">Permiso de cámara denegado</option>';
    }
  }

  async toggleCamera() {
    if (this.cameraStream) {
      this.stopCamera();
    } else {
      await this.initCamera();
    }
  }

  async initCamera() {
    const deviceId = this.cameraSelect.value;
    if (!deviceId) {
      await this.listCameras();
      if (!this.cameraSelect.value) return;
    }
    try {
      const constraints = {
        video: { deviceId: this.cameraSelect.value ? { exact: this.cameraSelect.value } : undefined }
      };
      this.cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
      this.cameraFeed.srcObject = this.cameraStream;
      this.cameraOff.classList.add("hidden");
      this.toggleCameraBtn.textContent = "Desconectar";
      this.toggleCameraBtn.classList.add("active");
      await this.listCameras();
    } catch (e) {
      console.warn("Error accediendo a cámara:", e);
      alert("No se pudo acceder a la cámara: " + e.message);
    }
  }

  stopCamera() {
    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach(t => t.stop());
      this.cameraStream = null;
    }
    this.cameraFeed.srcObject = null;
    this.cameraOff.classList.remove("hidden");
    this.toggleCameraBtn.textContent = "Conectar";
    this.toggleCameraBtn.classList.remove("active");
  }

  async onCameraChange() {
    if (this.cameraStream) {
      this.stopCamera();
      await this.initCamera();
    }
  }

  toggleTheme() {
    const root = document.documentElement;
    const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    root.setAttribute("data-theme", next);
    localStorage.setItem("primbio-theme", next);
    this._applyThemeUI();

    if (this.drawer) this.drawer.draw(this.lastData || { angle: 0, pos: 0, action: 0 });
    Object.values(this.charts).forEach((ch) => ch && ch.draw());
  }

  _applyThemeUI() {
    const theme = document.documentElement.getAttribute("data-theme");
    const light = theme === "light";
    if (!this.themeToggle) return;
    this.themeToggle.querySelector(".theme-icon").textContent = light ? "☀" : "☾";
    this.themeToggle.querySelector(".nav-text").textContent = light ? "Claro" : "Oscuro";
  }
}

document.addEventListener("DOMContentLoaded", () => { new PendulumApp(); });