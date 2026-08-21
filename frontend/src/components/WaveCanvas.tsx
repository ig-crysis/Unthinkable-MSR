import { useEffect, useRef } from "react";

interface Particle {
  xn: number;
  off: number;
  jx: number;
  r: number;
  seed: number;
  speed: number;
}
interface Star {
  xn: number;
  yn: number;
  r: number;
  a: number;
  seed: number;
}

const TAU = Math.PI * 2;
const PARTICLE_COUNT = 9600;
const STAR_COUNT = 160;

function buildParticles(): Particle[] {
  const particles: Particle[] = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      xn: Math.random() * 1.16 - 0.08,
      off: Math.random() - Math.random(),
      jx: (Math.random() - 0.5) * 6,
      r: 0.6 + Math.random() * 1.3,
      seed: Math.random() * TAU,
      speed: 0.5 + Math.random() * 0.7,
    });
  }
  return particles;
}
function buildStars(): Star[] {
  const stars: Star[] = [];
  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      xn: Math.random(),
      yn: Math.random(),
      r: 0.5 + Math.random() * 1.1,
      a: 0.15 + Math.random() * 0.4,
      seed: Math.random() * TAU,
    });
  }
  return stars;
}

export default function WaveCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const wrap = canvas?.parentElement;
    if (!canvas || !wrap) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const particles = buildParticles();
    const stars = buildStars();

    let W = 0;
    let H = 0;
    let DPR = 1;
    let t = 0;
    let lastTime = 0;
    let raf = 0;

    function resize() {
      const rect = wrap!.getBoundingClientRect();
      DPR = Math.min(window.devicePixelRatio || 1, 1.6);
      W = Math.max(1, Math.round(rect.width));
      H = Math.max(1, Math.round(rect.height));
      canvas!.width = Math.round(W * DPR);
      canvas!.height = Math.round(H * DPR);
      canvas!.style.width = `${W}px`;
      canvas!.style.height = `${H}px`;
      ctx!.setTransform(DPR, 0, 0, DPR, 0, 0);
    }

    function envelope(xn: number) {
      const c = Math.min(Math.max(xn, 0), 1);
      return 0.55 + 0.45 * Math.sin(Math.PI * c);
    }
    function wavePhase(xn: number, time: number) {
      return Math.PI * 0.5 + xn * Math.PI + time * 0.16;
    }
    function spineY(xn: number, time: number) {
      const amp = H * 0.26 * envelope(xn);
      return H * 0.5 + Math.sin(wavePhase(xn, time)) * amp;
    }
    function thicknessFactor(xn: number, time: number) {
      return 0.16 + 0.84 * Math.abs(Math.sin(wavePhase(xn, time)));
    }

    function draw(time: number) {
      if (!lastTime) lastTime = time;
      const dt = Math.min((time - lastTime) / 1000, 0.05);
      lastTime = time;
      if (!reduceMotion) t += dt;

      ctx!.clearRect(0, 0, W, H);
      if (W < 2 || H < 2) return;

      ctx!.globalCompositeOperation = "source-over";
      ctx!.fillStyle = "#ffffff";
      for (const st of stars) {
        const tw = 0.7 + 0.3 * Math.sin(t * 0.8 + st.seed);
        ctx!.globalAlpha = st.a * tw;
        ctx!.fillRect(st.xn * W - st.r, st.yn * H - st.r, st.r * 2, st.r * 2);
      }

      const maxThickness = H * 0.24;
      ctx!.globalCompositeOperation = "lighter";
      ctx!.fillStyle = "#eef1f6";
      for (const p of particles) {
        const xn = p.xn;
        const env = envelope(xn);
        const thick = thicknessFactor(xn, t);
        const halfW = maxThickness * env * thick;
        const y = spineY(xn, t) + p.off * halfW;
        const x = xn * W + p.jx;
        if (x < -8 || x > W + 8) continue;
        const density = 1 - Math.min(Math.abs(p.off), 1);
        const twinkle = 0.75 + 0.25 * Math.sin(t * p.speed + p.seed);
        const alpha = density * (0.18 + thick * 0.5) * env * twinkle;
        if (alpha <= 0.01) continue;
        ctx!.globalAlpha = Math.min(alpha, 0.8);
        ctx!.fillRect(x - p.r, y - p.r, p.r * 2, p.r * 2);
      }

      ctx!.globalAlpha = 1;
      ctx!.globalCompositeOperation = "source-over";
    }

    function frame(ts: number) {
      draw(ts);
      raf = requestAnimationFrame(frame);
    }

    let resizePending = false;
    function scheduleResize() {
      if (resizePending) return;
      resizePending = true;
      requestAnimationFrame(() => {
        resizePending = false;
        resize();
        if (reduceMotion) draw(performance.now());
      });
    }

    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(scheduleResize) : null;
    ro?.observe(wrap);
    if (!ro) window.addEventListener("resize", scheduleResize);

    function handleVisibility() {
      if (reduceMotion) return;
      if (document.hidden) {
        if (raf) cancelAnimationFrame(raf);
        raf = 0;
        lastTime = 0;
      } else if (!raf) {
        raf = requestAnimationFrame(frame);
      }
    }
    document.addEventListener("visibilitychange", handleVisibility);

    resize();
    if (reduceMotion) {
      draw(performance.now());
    } else {
      raf = requestAnimationFrame(frame);
    }

    return () => {
      if (raf) cancelAnimationFrame(raf);
      ro?.disconnect();
      if (!ro) window.removeEventListener("resize", scheduleResize);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, []);

  return <canvas ref={canvasRef} id="wave-canvas" aria-hidden="true" />;
}
