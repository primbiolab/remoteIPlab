class PendulumDrawer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.setupCanvas();
    window.addEventListener("resize", () => this.setupCanvas());
  }

  cssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  colors() {
    return {
      bg: this.cssVar("--canvas-bg", "#0f0e0c"),
      panel: this.cssVar("--canvas-panel", "#1c1a16"),
      surface: this.cssVar("--canvas-surface", "#2a2520"),
      overlay: this.cssVar("--canvas-overlay", "#3d3830"),
      muted: this.cssVar("--canvas-muted", "#7a7268"),
      fg: this.cssVar("--canvas-fg", "#f0ece4"),
      accent: this.cssVar("--accent", "#e0571c"),
      green: this.cssVar("--green", "#3f9468"),
      red: this.cssVar("--red", "#e0573f"),
      peach: this.cssVar("--peach", "#e0a020"),
      yellow: this.cssVar("--yellow", "#e0a020"),
    };
  }

  setupCanvas() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const w = Math.max(Math.floor(rect.width - 24), 100);
    const h = Math.max(Math.min(420, Math.floor(w * 0.5)), 160);
    this.canvas.style.width = w + "px";
    this.canvas.style.height = h + "px";
    this.canvas.width = w * this.dpr;
    this.canvas.height = h * this.dpr;
    this.ctx.scale(this.dpr, this.dpr);
    this.W = w;
    this.H = h;
  }

  draw(data) {
    const ctx = this.ctx;
    const w = this.W, h = this.H;
    ctx.clearRect(0, 0, w, h);

    const cols = this.colors();

    const margin = 50;
    const trackL = margin, trackR = w - margin, trackW = trackR - trackL;
    const cartY = h * 0.58;
    let angleDeg = -(data.angle || 0);
    let pos = data.pos || 0;

    const limitPulses = data.pos_limit_pulses || 5000;
    const maxPosCm = (2 * Math.PI * limitPulses / 2400) * 1.2;
    pos = Math.max(-1, Math.min(1, pos / maxPosCm));

    let xPix = trackL + ((pos + 1) / 2) * trackW;
    xPix = Math.max(trackL + 25, Math.min(trackR - 25, xPix));

    const cartW = 70, cartH = 32;
    const cartX = xPix - cartW / 2;

    ctx.save();

    ctx.fillStyle = cols.bg;
    ctx.fillRect(0, 0, w, h);

    ctx.beginPath();
    ctx.strokeStyle = cols.overlay;
    ctx.lineWidth = 2;
    ctx.moveTo(trackL, cartY + cartH + 12);
    ctx.lineTo(trackR, cartY + cartH + 12);
    ctx.stroke();

    ctx.beginPath();
    ctx.strokeStyle = cols.surface;
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.moveTo(trackL, cartY + cartH + 8);
    ctx.lineTo(trackR, cartY + cartH + 8);
    ctx.stroke();
    ctx.setLineDash([]);

    const limitPx = (data.pos_limit_pulses || 5000);
    const limitFrac = Math.min(1, limitPx / 5000);
    const limitLeftPx = trackL + (1 - limitFrac) / 2 * trackW;
    const limitRightPx = trackR - (1 - limitFrac) / 2 * trackW;
    ctx.strokeStyle = cols.yellow;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([3, 4]);
    ctx.beginPath();
    ctx.moveTo(limitLeftPx, cartY - 8);
    ctx.lineTo(limitLeftPx, cartY + cartH + 22);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(limitRightPx, cartY - 8);
    ctx.lineTo(limitRightPx, cartY + cartH + 22);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.fillStyle = cols.yellow;
    ctx.fillText(`Límite: ${limitPx} pulsos`, trackL, cartY + cartH + 40);

    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.fillRect(cartX + 2, cartY + 2, cartW, cartH);

    ctx.fillStyle = cols.panel;
    ctx.strokeStyle = cols.surface;
    ctx.lineWidth = 1.5;
    const rad = 4;
    ctx.beginPath();
    ctx.moveTo(cartX + rad, cartY);
    ctx.lineTo(cartX + cartW - rad, cartY);
    ctx.quadraticCurveTo(cartX + cartW, cartY, cartX + cartW, cartY + rad);
    ctx.lineTo(cartX + cartW, cartY + cartH - rad);
    ctx.quadraticCurveTo(cartX + cartW, cartY + cartH, cartX + cartW - rad, cartY + cartH);
    ctx.lineTo(cartX + rad, cartY + cartH);
    ctx.quadraticCurveTo(cartX, cartY + cartH, cartX, cartY + cartH - rad);
    ctx.lineTo(cartX, cartY + rad);
    ctx.quadraticCurveTo(cartX, cartY, cartX + rad, cartY);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    const wr = 8;
    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.beginPath();
    ctx.arc(cartX + cartW * 0.22 + 1, cartY + cartH + wr + 1, wr, 0, 2 * Math.PI);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cartX + cartW * 0.78 + 1, cartY + cartH + wr + 1, wr, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = cols.overlay;
    ctx.strokeStyle = cols.surface;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cartX + cartW * 0.22, cartY + cartH + wr, wr, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cartX + cartW * 0.78, cartY + cartH + wr, wr, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = cols.panel;
    ctx.beginPath();
    ctx.arc(cartX + cartW * 0.22, cartY + cartH + wr, 3, 0, 2 * Math.PI);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cartX + cartW * 0.78, cartY + cartH + wr, 3, 0, 2 * Math.PI);
    ctx.fill();

    const theta = angleDeg * Math.PI / 180;
    const pivotX = xPix;
    const pivotY = cartY - 6;
    const rodLen = Math.min(h * 0.28, 160);
    const bobX = pivotX + rodLen * Math.sin(theta);
    const bobY = pivotY - rodLen * Math.cos(theta);

    ctx.shadowColor = "rgba(0,0,0,0.2)";
    ctx.shadowBlur = 4;
    const grad = ctx.createLinearGradient(pivotX, pivotY, bobX, bobY);
    grad.addColorStop(0, cols.accent);
    grad.addColorStop(1, cols.fg);
    ctx.beginPath();
    ctx.strokeStyle = grad;
    ctx.lineWidth = 3.5;
    ctx.moveTo(pivotX, pivotY);
    ctx.lineTo(bobX, bobY);
    ctx.stroke();

    ctx.shadowBlur = 2;
    ctx.fillStyle = cols.accent;
    ctx.beginPath();
    ctx.arc(pivotX, pivotY, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = cols.fg;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(pivotX, pivotY, 7, 0, 2 * Math.PI);
    ctx.stroke();

    const bobR = Math.max(10, Math.min(14, rodLen * 0.12));
    const rg = ctx.createRadialGradient(bobX - 2, bobY - 2, 2, bobX, bobY, bobR);
    rg.addColorStop(0, cols.peach);
    rg.addColorStop(1, "#c04a15");
    ctx.shadowBlur = 4;
    ctx.fillStyle = rg;
    ctx.beginPath();
    ctx.arc(bobX, bobY, bobR, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = cols.overlay;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(bobX, bobY, bobR, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,0.2)";
    ctx.beginPath();
    ctx.arc(bobX - 2, bobY - 3, 3, 0, 2 * Math.PI);
    ctx.fill();
    ctx.restore();

    ctx.font = '12px "JetBrains Mono", monospace';
    ctx.fillStyle = cols.muted;
    ctx.fillText(`Ángulo: ${angleDeg.toFixed(1)}°`, 12, 22);
    ctx.fillText(`Pos: ${pos.toFixed(3)}`, 12, 40);
    ctx.fillText(`Control: ${(data.action || 0).toFixed(2)} V`, 12, 58);

    const a = Math.abs(angleDeg);
    ctx.font = 'bold 13px "Segoe UI", sans-serif';
    if (a < 10) { ctx.fillStyle = cols.green; ctx.fillText("✓ Estable", w - 90, 22); }
    else if (a > 45) { ctx.fillStyle = cols.red; ctx.fillText("⚠ Inestable", w - 90, 22); }
    else if (a > 20) { ctx.fillStyle = cols.yellow; ctx.fillText("⚡ Swing-up", w - 90, 22); }
  }
  
}
