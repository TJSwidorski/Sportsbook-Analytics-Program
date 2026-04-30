// Geometric mesh background — animated nodes, edges, optional scroll reactivity.
// Drop one of: <MeshBg variant="precise" />, <MeshBg variant="neon" />, <MeshBg variant="luxe" />
// Each mounts a canvas absolutely-positioned to fill the parent (parent must be position: relative/absolute).

const MeshBg = ({ variant = "neon", density = 75, scrollEl = null, accentA, accentB, dark = false }) => {
  const canvasRef = React.useRef(null);
  const rafRef = React.useRef(0);
  const stateRef = React.useRef({ nodes: [], scrollY: 0, t: 0 });

  // theme
  const palette = React.useMemo(() => {
    const variants = {
      precise: {
        edge: dark ? "rgba(180,200,220,0.18)" : "rgba(20,30,45,0.22)",
        node: dark ? "rgba(220,235,250,0.7)" : "rgba(20,30,45,0.55)",
        glow: accentA || "oklch(0.62 0.2 250)",
        halo: accentB || "oklch(0.7 0.18 145)",
      },
      neon: {
        edge: dark ? "rgba(120,180,255,0.28)" : "rgba(60,120,200,0.22)",
        node: dark ? "rgba(180,220,255,0.9)" : "rgba(40,90,170,0.55)",
        glow: accentA || "oklch(0.7 0.2 250)",
        halo: accentB || "oklch(0.72 0.2 145)",
      },
      luxe: {
        edge: dark ? "rgba(220,210,190,0.18)" : "rgba(80,75,65,0.16)",
        node: dark ? "rgba(240,230,210,0.6)" : "rgba(80,75,65,0.4)",
        glow: accentA || "oklch(0.78 0.1 80)",
        halo: accentB || "oklch(0.7 0.12 145)",
      },
    };
    return variants[variant] || variants.neon;
  }, [variant, dark, accentA, accentB]);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      canvas.width = r.width * dpr;
      canvas.height = r.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const cols = variant === "luxe" ? 8 : variant === "precise" ? 14 : 12;
      const rows = variant === "luxe" ? 6 : variant === "precise" ? 10 : 8;
      const w = r.width, h = r.height;
      const nodes = [];
      for (let i = 0; i <= cols; i++) {
        for (let j = 0; j <= rows; j++) {
          const jitter = variant === "precise" ? 0.08 : variant === "luxe" ? 0.18 : 0.32;
          const baseX = (i / cols) * w;
          const baseY = (j / rows) * h;
          nodes.push({
            bx: baseX,
            by: baseY,
            ox: (Math.random() - 0.5) * w / cols * jitter,
            oy: (Math.random() - 0.5) * h / rows * jitter,
            phase: Math.random() * Math.PI * 2,
            speed: 0.0003 + Math.random() * 0.0006,
            amp: variant === "precise" ? 4 : variant === "luxe" ? 8 : 14,
            x: 0, y: 0,
            pulse: Math.random(),
          });
        }
      }
      stateRef.current.nodes = nodes;
      stateRef.current.cols = cols;
      stateRef.current.rows = rows;
      stateRef.current.w = w;
      stateRef.current.h = h;
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const onScroll = () => {
      const target = scrollEl?.current || scrollEl || window;
      stateRef.current.scrollY = target === window ? window.scrollY : target.scrollTop;
    };
    const target = scrollEl?.current || scrollEl;
    if (target) target.addEventListener("scroll", onScroll, { passive: true });
    else window.addEventListener("scroll", onScroll, { passive: true });

    const tick = () => {
      const s = stateRef.current;
      s.t += 1;
      const { nodes, cols, rows, w, h } = s;
      if (!nodes || !w) { rafRef.current = requestAnimationFrame(tick); return; }
      ctx.clearRect(0, 0, w, h);

      const sy = s.scrollY * 0.05;

      // update positions
      for (const n of nodes) {
        const drift = Math.sin(s.t * n.speed + n.phase) * n.amp;
        const drift2 = Math.cos(s.t * n.speed * 0.7 + n.phase) * n.amp;
        n.x = n.bx + n.ox + drift + Math.sin(sy * 0.01 + n.phase) * 6;
        n.y = n.by + n.oy + drift2 - sy * 0.15;
      }

      // edges (only between grid neighbors for clean look)
      ctx.strokeStyle = palette.edge;
      ctx.lineWidth = variant === "precise" ? 0.5 : 0.7;
      for (let i = 0; i <= cols; i++) {
        for (let j = 0; j <= rows; j++) {
          const idx = i * (rows + 1) + j;
          const n = nodes[idx];
          if (!n) continue;
          // right neighbor
          if (i < cols) {
            const r = nodes[(i + 1) * (rows + 1) + j];
            if (r) { ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(r.x, r.y); ctx.stroke(); }
          }
          // down neighbor
          if (j < rows) {
            const d = nodes[i * (rows + 1) + (j + 1)];
            if (d) { ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(d.x, d.y); ctx.stroke(); }
          }
          // diagonal for neon variant
          if (variant === "neon" && i < cols && j < rows && (i + j) % 2 === 0) {
            const dg = nodes[(i + 1) * (rows + 1) + (j + 1)];
            if (dg) {
              ctx.save();
              ctx.strokeStyle = palette.edge.replace(/[\d.]+\)$/, "0.08)");
              ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(dg.x, dg.y); ctx.stroke();
              ctx.restore();
            }
          }
        }
      }

      // nodes
      for (const n of nodes) {
        const pulse = (Math.sin(s.t * 0.02 + n.phase * 3) + 1) * 0.5;
        ctx.fillStyle = palette.node;
        ctx.beginPath();
        ctx.arc(n.x, n.y, 1.2 + pulse * 0.6, 0, Math.PI * 2);
        ctx.fill();
      }

      // traveling lights along edges (neon + luxe only)
      if (variant !== "precise") {
        const numTravel = variant === "neon" ? 8 : 4;
        for (let k = 0; k < numTravel; k++) {
          const seed = (s.t * 0.003 + k * 0.7) % 1;
          const i = Math.floor((k * 37) % cols);
          const j = Math.floor((k * 53) % rows);
          const a = nodes[i * (rows + 1) + j];
          const b = nodes[(i + 1) * (rows + 1) + j];
          if (!a || !b) continue;
          const x = a.x + (b.x - a.x) * seed;
          const y = a.y + (b.y - a.y) * seed;
          const grad = ctx.createRadialGradient(x, y, 0, x, y, 60);
          grad.addColorStop(0, k % 2 ? palette.glow : palette.halo);
          grad.addColorStop(1, "transparent");
          ctx.globalAlpha = variant === "neon" ? 0.45 : 0.25;
          ctx.fillStyle = grad;
          ctx.beginPath(); ctx.arc(x, y, 60, 0, Math.PI * 2); ctx.fill();
          ctx.globalAlpha = 1;
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      if (target) target.removeEventListener("scroll", onScroll);
      else window.removeEventListener("scroll", onScroll);
    };
  }, [variant, palette, scrollEl]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
    />
  );
};

window.MeshBg = MeshBg;
