// DIRECTION 2: AXIOM MESH
// Tech-forward neon. Editorial sans (Space Grotesk) + JetBrains Mono.
// Heavy mesh background, glowing glass cards, more dramatic visual treatment.

const MeshApp = ({ width = 1440, height = 900 }) => {
  const [tab, setTab] = React.useState("home");
  const [dark, setDark] = React.useState(false);
  const [selectedPick, setSelectedPick] = React.useState(null);
  const scrollRef = React.useRef(null);

  const palette = dark ? {
    bg: "#070a14",
    bgGrad: "radial-gradient(ellipse at 20% 0%, #0e1530 0%, #070a14 50%)",
    surface: "rgba(20,28,50,0.55)",
    surface2: "rgba(30,40,70,0.65)",
    border: "rgba(120,180,255,0.18)",
    border2: "rgba(120,180,255,0.32)",
    text: "#e6edff",
    muted: "#7a8aae",
    accent: "oklch(0.78 0.2 250)",
    accentSoft: "oklch(0.5 0.18 250 / 0.4)",
    win: "oklch(0.78 0.2 145)",
    loss: "oklch(0.7 0.22 25)",
    glow: "oklch(0.78 0.2 250 / 0.5)",
  } : {
    bg: "#f6f8fd",
    bgGrad: "radial-gradient(ellipse at 20% 0%, #eef2fb 0%, #f6f8fd 60%)",
    surface: "rgba(255,255,255,0.7)",
    surface2: "rgba(255,255,255,0.85)",
    border: "rgba(40,90,170,0.14)",
    border2: "rgba(40,90,170,0.28)",
    text: "#0c1530",
    muted: "#5a6885",
    accent: "oklch(0.55 0.2 250)",
    accentSoft: "oklch(0.7 0.16 250 / 0.3)",
    win: "oklch(0.55 0.18 145)",
    loss: "oklch(0.55 0.22 25)",
    glow: "oklch(0.7 0.2 250 / 0.4)",
  };

  const fontDisplay = "'Space Grotesk', system-ui, sans-serif";
  const fontMono = "'JetBrains Mono', ui-monospace, monospace";

  return (
    <div style={{
      width, height, background: palette.bgGrad, color: palette.text,
      fontFamily: fontDisplay, position: "relative", overflow: "hidden",
      display: "flex", flexDirection: "column", fontSize: 14,
    }}>
      {/* Header */}
      <header style={{
        height: 64, padding: "0 32px", display: "flex", alignItems: "center", gap: 40,
        position: "relative", zIndex: 5,
        background: dark ? "rgba(7,10,20,0.6)" : "rgba(246,248,253,0.6)",
        backdropFilter: "blur(16px)",
        borderBottom: `1px solid ${palette.border}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 32, height: 32, position: "relative",
          }}>
            <svg viewBox="0 0 32 32" style={{ position: "absolute", inset: 0 }}>
              <defs>
                <radialGradient id="meshlogo" cx="50%" cy="50%">
                  <stop offset="0%" stopColor={palette.accent} stopOpacity="1"/>
                  <stop offset="100%" stopColor={palette.accent} stopOpacity="0.2"/>
                </radialGradient>
              </defs>
              <circle cx="6" cy="8" r="2" fill={palette.accent}/>
              <circle cx="26" cy="8" r="2" fill={palette.accent}/>
              <circle cx="16" cy="16" r="3" fill="url(#meshlogo)"/>
              <circle cx="6" cy="24" r="2" fill={palette.accent}/>
              <circle cx="26" cy="24" r="2" fill={palette.accent}/>
              <line x1="6" y1="8" x2="16" y2="16" stroke={palette.accent} strokeWidth="1"/>
              <line x1="26" y1="8" x2="16" y2="16" stroke={palette.accent} strokeWidth="1"/>
              <line x1="6" y1="24" x2="16" y2="16" stroke={palette.accent} strokeWidth="1"/>
              <line x1="26" y1="24" x2="16" y2="16" stroke={palette.accent} strokeWidth="1"/>
            </svg>
          </div>
          <div style={{ fontSize: 17, fontWeight: 600, letterSpacing: -0.3 }}>Axiom</div>
        </div>
        <nav style={{ display: "flex", gap: 4 }}>
          {[
            { id: "home", label: "Overview" },
            { id: "today", label: "Today's Picks" },
            { id: "history", label: "Performance" },
            { id: "backtest", label: "Backtests" },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: "8px 16px", borderRadius: 999,
              background: tab === t.id ? palette.surface : "transparent",
              border: tab === t.id ? `1px solid ${palette.border2}` : "1px solid transparent",
              color: tab === t.id ? palette.text : palette.muted,
              cursor: "pointer", fontSize: 13, fontWeight: 500, fontFamily: fontDisplay,
              backdropFilter: tab === t.id ? "blur(8px)" : "none",
            }}>{t.label}</button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={() => setDark(!dark)} style={{
            width: 52, height: 26, borderRadius: 999, background: palette.surface,
            border: `1px solid ${palette.border2}`, position: "relative", cursor: "pointer", padding: 0,
          }}>
            <div style={{
              position: "absolute", top: 2, left: dark ? 28 : 2,
              width: 20, height: 20, borderRadius: "50%",
              background: `linear-gradient(135deg, ${palette.accent}, ${palette.win})`,
              transition: "left 0.2s", boxShadow: `0 0 12px ${palette.glow}`,
            }} />
          </button>
          <button style={{
            padding: "8px 18px", borderRadius: 999,
            background: `linear-gradient(135deg, ${palette.accent}, ${palette.win})`,
            color: dark ? "#070a14" : "#fff", fontWeight: 600, fontSize: 13,
            border: "none", cursor: "pointer", fontFamily: fontDisplay,
            boxShadow: `0 4px 24px ${palette.glow}`,
          }}>Get Access</button>
        </div>
      </header>

      <div ref={scrollRef} style={{ flex: 1, overflow: "auto", position: "relative" }}>
        <MeshBg variant="neon" dark={dark} scrollEl={scrollRef} accentA={palette.accent} accentB={palette.win} />
        <div style={{ position: "relative", zIndex: 1 }}>
          {tab === "home" && <MeshHome palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} setTab={setTab} />}
          {tab === "today" && <MeshToday palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} selectedPick={selectedPick} setSelectedPick={setSelectedPick} />}
          {tab === "history" && <MeshHistory palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} />}
          {tab === "backtest" && <MeshBacktest palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} />}
        </div>
      </div>
    </div>
  );
};

// Glass card primitive with traveling light
const MeshGlassCard = ({ children, palette, padding = 24, glow = true, onClick, style = {} }) => (
  <div onClick={onClick} style={{
    background: palette.surface,
    border: `1px solid ${palette.border}`,
    borderRadius: 18,
    padding,
    position: "relative",
    backdropFilter: "blur(24px)",
    WebkitBackdropFilter: "blur(24px)",
    cursor: onClick ? "pointer" : "default",
    boxShadow: glow ? `0 1px 0 rgba(255,255,255,0.2) inset, 0 20px 60px -30px ${palette.glow}, 0 4px 20px -10px ${palette.glow}` : "0 1px 0 rgba(255,255,255,0.2) inset",
    overflow: "hidden",
    ...style,
  }}>
    {glow && (
      <div style={{
        position: "absolute", inset: -1, borderRadius: 18,
        background: `radial-gradient(ellipse 70% 60% at 50% -10%, ${palette.accentSoft}, transparent 70%)`,
        pointerEvents: "none",
      }} />
    )}
    <div style={{ position: "relative" }}>{children}</div>
  </div>
);

// === HOME ===
const MeshHome = ({ palette, fontDisplay, fontMono, setTab }) => (
  <div style={{ padding: "72px 32px 96px" }}>
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 10, padding: "6px 14px", borderRadius: 999, background: palette.surface, border: `1px solid ${palette.border}`, fontFamily: fontMono, fontSize: 11, color: palette.muted, marginBottom: 28, backdropFilter: "blur(8px)" }}>
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: palette.accent, boxShadow: `0 0 8px ${palette.accent}` }} />
        Model v4.2.1 · 8 picks live for today
      </div>

      <h1 style={{
        fontSize: 92, lineHeight: 0.92, fontWeight: 500, letterSpacing: -3.5,
        margin: "0 0 24px", maxWidth: 1000,
      }}>
        Sports betting,<br/>
        solved as a <span style={{
          background: `linear-gradient(120deg, ${palette.accent}, ${palette.win})`,
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          fontStyle: "italic",
        }}>network problem.</span>
      </h1>
      <p style={{ fontSize: 19, lineHeight: 1.5, color: palette.muted, maxWidth: 580, margin: "0 0 56px" }}>
        Axiom maps every team, player, line and market into one connected graph — then walks it to find mispriced bets across seven leagues.
      </p>

      {/* hero metrics — three glass cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 80 }}>
        {[
          { k: "Win Rate", v: "65%", sub: "10,243 picks tracked" },
          { k: "Up Units", v: "+71", sub: "season to date" },
          { k: "Picks Tracked", v: "10K+", sub: "since Sept 2019" },
        ].map((m, i) => (
          <MeshGlassCard key={i} palette={palette} padding={28}>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 16 }}>{m.k}</div>
            <div style={{ fontSize: 64, fontWeight: 500, lineHeight: 1, letterSpacing: -2, marginBottom: 10,
              background: `linear-gradient(135deg, ${palette.text}, ${palette.accent})`,
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>{m.v}</div>
            <div style={{ fontSize: 13, color: palette.muted }}>{m.sub}</div>
          </MeshGlassCard>
        ))}
      </div>

      {/* network section */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 32, marginBottom: 80, alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.accent, letterSpacing: 2, marginBottom: 16 }}>◆ THE NETWORK</div>
          <h2 style={{ fontSize: 44, lineHeight: 1.05, fontWeight: 500, margin: "0 0 20px", letterSpacing: -1.5 }}>
            14 million data points.<br/>One graph.
          </h2>
          <p style={{ fontSize: 15, lineHeight: 1.6, color: palette.muted, marginBottom: 24 }}>
            Every player, team, line, market and matchup is a node. Edges encode rest, travel, weather, lineup, momentum, public money, and 41 other features. The model walks the graph to find inefficiencies the book missed.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {["Bayesian ensemble", "2,000 Monte Carlo paths", "Closing line tracked", "Kelly-sized stakes"].map(t => (
              <div key={t} style={{ padding: "6px 12px", borderRadius: 999, background: palette.surface, border: `1px solid ${palette.border}`, fontFamily: fontMono, fontSize: 11, color: palette.muted }}>{t}</div>
            ))}
          </div>
        </div>
        <MeshGlassCard palette={palette} padding={0} style={{ height: 360 }}>
          <NetworkViz palette={palette} fontMono={fontMono} />
        </MeshGlassCard>
      </div>

      {/* board preview */}
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 20 }}>
        <h2 style={{ fontSize: 32, fontWeight: 500, margin: 0, letterSpacing: -0.8 }}>Today's board</h2>
        <button onClick={() => setTab("today")} style={{ background: "transparent", border: "none", color: palette.accent, fontFamily: fontMono, fontSize: 12, cursor: "pointer", letterSpacing: 1 }}>VIEW ALL 8 →</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
        {TODAYS_GAMES.slice(0, 4).map((g, i) => (
          <MeshGameCard key={i} g={g} palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} onClick={() => setTab("today")} />
        ))}
      </div>
    </div>
  </div>
);

const NetworkViz = ({ palette, fontMono }) => {
  // static-ish network illustration
  const nodes = [
    { x: 80, y: 60, label: "BOS", size: 22 },
    { x: 220, y: 100, label: "DEN", size: 26 },
    { x: 360, y: 70, label: "LAL", size: 18 },
    { x: 480, y: 140, label: "PHX", size: 20 },
    { x: 60, y: 200, label: "MIA", size: 16 },
    { x: 180, y: 240, label: "GSW", size: 22 },
    { x: 320, y: 220, label: "OKC", size: 20 },
    { x: 460, y: 290, label: "MIL", size: 18 },
    { x: 130, y: 320, label: "BUF", size: 16 },
    { x: 280, y: 320, label: "KC", size: 24 },
  ];
  const edges = [
    [0, 1], [1, 2], [2, 3], [1, 5], [4, 5], [5, 6], [6, 7], [3, 7],
    [5, 8], [8, 9], [6, 9], [1, 6], [0, 4], [3, 6],
  ];
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <svg viewBox="0 0 540 360" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <radialGradient id="nodeglow">
            <stop offset="0%" stopColor={palette.accent} stopOpacity="1" />
            <stop offset="100%" stopColor={palette.accent} stopOpacity="0" />
          </radialGradient>
        </defs>
        {edges.map(([a, b], i) => (
          <line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y}
            stroke={palette.accent} strokeOpacity="0.35" strokeWidth="1" />
        ))}
        {nodes.map((n, i) => (
          <g key={i}>
            <circle cx={n.x} cy={n.y} r={n.size + 8} fill="url(#nodeglow)" opacity="0.5" />
            <circle cx={n.x} cy={n.y} r={n.size} fill={palette.surface2} stroke={palette.accent} strokeWidth="1" />
            <text x={n.x} y={n.y + 3} textAnchor="middle" fontFamily={fontMono} fontSize="9" fill={palette.text} fontWeight="600">{n.label}</text>
          </g>
        ))}
      </svg>
      <div style={{ position: "absolute", top: 16, left: 16, fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
        ◆ LIVE GRAPH · 1,247 NODES · 8,392 EDGES
      </div>
    </div>
  );
};

const MeshGameCard = ({ g, palette, fontDisplay, fontMono, onClick }) => (
  <MeshGlassCard palette={palette} padding={20} onClick={onClick}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
      <div style={{ padding: "3px 8px", borderRadius: 6, background: palette.surface2, fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>{g.league}</div>
      <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted }}>{g.time}</div>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
      <div style={{ width: 28, height: 28, borderRadius: 8, background: palette.surface2, border: `1px solid ${palette.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: fontMono, fontSize: 9, fontWeight: 700 }}>{g.awayAbbr}</div>
      <div style={{ fontSize: 13, fontWeight: 500 }}>{g.away}</div>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
      <div style={{ width: 28, height: 28, borderRadius: 8, background: palette.surface2, border: `1px solid ${palette.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: fontMono, fontSize: 9, fontWeight: 700 }}>{g.homeAbbr}</div>
      <div style={{ fontSize: 13, fontWeight: 500 }}>{g.home}</div>
    </div>
    <div style={{ paddingTop: 16, borderTop: `1px solid ${palette.border}`, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
      <div>
        <div style={{ fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 1, marginBottom: 4 }}>PICK</div>
        <div style={{ fontSize: 16, fontWeight: 600, color: palette.accent }}>{g.pick}</div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 1, marginBottom: 4 }}>EDGE</div>
        <div style={{ fontSize: 16, fontWeight: 600 }}>{g.edge}</div>
      </div>
    </div>
  </MeshGlassCard>
);

// === TODAY ===
const MeshToday = ({ palette, fontDisplay, fontMono, selectedPick, setSelectedPick }) => (
  <div style={{ padding: "48px 32px", maxWidth: 1376, margin: "0 auto", display: "grid", gridTemplateColumns: selectedPick ? "1fr 440px" : "1fr", gap: 24 }}>
    <div>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.accent, letterSpacing: 2, marginBottom: 8 }}>◆ TUE 04.28.2026</div>
        <h2 style={{ fontSize: 44, fontWeight: 500, margin: 0, letterSpacing: -1.5 }}>Today's picks</h2>
      </div>
      <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
        {["All sports", "NBA", "NFL", "MLB", "NHL", "NCAA", "Soccer"].map((t, i) => (
          <div key={t} style={{
            padding: "6px 14px", borderRadius: 999,
            background: i === 0 ? palette.text : palette.surface,
            color: i === 0 ? palette.bg : palette.muted,
            border: `1px solid ${palette.border}`, fontSize: 12, fontWeight: 500, cursor: "pointer",
          }}>{t}</div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: selectedPick ? "repeat(2, 1fr)" : "repeat(4, 1fr)", gap: 16 }}>
        {TODAYS_GAMES.map((g, i) => (
          <MeshGameCard key={i} g={g} palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} onClick={() => setSelectedPick(g)} />
        ))}
      </div>
    </div>

    {selectedPick && (
      <div style={{ position: "sticky", top: 0, alignSelf: "start" }}>
        <MeshGlassCard palette={palette} padding={28}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.accent, letterSpacing: 2 }}>◆ PICK DETAIL</div>
            <button onClick={() => setSelectedPick(null)} style={{ background: "transparent", border: "none", color: palette.muted, cursor: "pointer", fontSize: 22, lineHeight: 1 }}>×</button>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
            <div style={{ textAlign: "center", flex: 1 }}>
              <div style={{ width: 56, height: 56, borderRadius: 14, background: palette.surface2, border: `1px solid ${palette.border}`, display: "inline-flex", alignItems: "center", justifyContent: "center", fontFamily: fontMono, fontWeight: 700, fontSize: 14, marginBottom: 10 }}>{selectedPick.awayAbbr}</div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{selectedPick.away}</div>
            </div>
            <div style={{ fontFamily: fontMono, fontSize: 12, color: palette.muted, padding: "0 12px" }}>vs</div>
            <div style={{ textAlign: "center", flex: 1 }}>
              <div style={{ width: 56, height: 56, borderRadius: 14, background: palette.surface2, border: `1px solid ${palette.border}`, display: "inline-flex", alignItems: "center", justifyContent: "center", fontFamily: fontMono, fontWeight: 700, fontSize: 14, marginBottom: 10 }}>{selectedPick.homeAbbr}</div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{selectedPick.home}</div>
            </div>
          </div>

          <div style={{ background: palette.surface2, border: `1px solid ${palette.border}`, borderRadius: 14, padding: 20, marginBottom: 20 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 8 }}>RECOMMENDED</div>
            <div style={{ fontSize: 32, fontWeight: 600, color: palette.accent, letterSpacing: -0.5, marginBottom: 16 }}>{selectedPick.pick}</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
              {[["Stake", `${selectedPick.units}u`], ["Edge", selectedPick.edge], ["Confidence", `${selectedPick.confidence}%`]].map(([k, v]) => (
                <div key={k}>
                  <div style={{ fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 1, marginBottom: 4 }}>{k.toUpperCase()}</div>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 14 }}>SIGNAL BREAKDOWN</div>
            {[
              { k: "Pace differential", v: 78 },
              { k: "Rest advantage", v: 64 },
              { k: "Closing line value", v: 82 },
              { k: "Lineup confidence", v: 91 },
            ].map(s => (
              <div key={s.k} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: palette.muted }}>{s.k}</span>
                  <span style={{ fontFamily: fontMono, fontWeight: 600 }}>{s.v}</span>
                </div>
                <div style={{ height: 4, background: palette.surface2, borderRadius: 999, position: "relative", overflow: "hidden" }}>
                  <div style={{ position: "absolute", inset: 0, width: `${s.v}%`, background: `linear-gradient(90deg, ${palette.accent}, ${palette.win})`, borderRadius: 999 }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: palette.surface2, borderRadius: 12, padding: 16, fontSize: 12, lineHeight: 1.6, color: palette.muted, borderLeft: `2px solid ${palette.accent}` }}>
            Closing line value detected at -3.5; market drifting toward -2.5. Pace mismatch favors {selectedPick.homeAbbr} in transition. Confidence elevated post-lineup confirmation.
          </div>
        </MeshGlassCard>
      </div>
    )}
  </div>
);

// === HISTORY ===
const MeshHistory = ({ palette, fontDisplay, fontMono }) => {
  const max = Math.max(...PERFORMANCE_30D.map(d => d.units));
  const min = Math.min(0, ...PERFORMANCE_30D.map(d => d.units));
  return (
    <div style={{ padding: "48px 32px", maxWidth: 1376, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 32 }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.accent, letterSpacing: 2, marginBottom: 8 }}>◆ MODEL PERFORMANCE</div>
          <h2 style={{ fontSize: 44, fontWeight: 500, margin: 0, letterSpacing: -1.5 }}>Performance.</h2>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["7D", "30D", "90D", "YTD"].map((t, i) => (
            <div key={t} style={{
              padding: "6px 14px", borderRadius: 999,
              background: i === 1 ? palette.text : palette.surface,
              color: i === 1 ? palette.bg : palette.muted,
              border: `1px solid ${palette.border}`, fontSize: 12, fontWeight: 500, fontFamily: fontMono, cursor: "pointer", letterSpacing: 1,
            }}>{t}</div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { k: "WIN RATE", v: "65.4%", d: "+1.1pp" },
          { k: "PICKS", v: "187", d: "30D" },
          { k: "UNITS", v: "+18.4", d: "+24%" },
          { k: "ROI", v: "+19.6%", d: "+2.3pp" },
          { k: "EDGE", v: "3.7%", d: "+0.2pp" },
        ].map((m, i) => (
          <MeshGlassCard key={i} palette={palette} padding={20}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 10 }}>{m.k}</div>
            <div style={{ fontSize: 30, fontWeight: 500, letterSpacing: -1 }}>{m.v}</div>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.win, marginTop: 4 }}>↑ {m.d}</div>
          </MeshGlassCard>
        ))}
      </div>

      <MeshGlassCard palette={palette} padding={28} style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 4 }}>CUMULATIVE UNITS · 30D</div>
            <div style={{ fontSize: 28, fontWeight: 500, letterSpacing: -0.5 }}>+{PERFORMANCE_30D[PERFORMANCE_30D.length - 1].units.toFixed(2)}</div>
          </div>
        </div>
        <div style={{ height: 240 }}>
          <svg viewBox="0 0 800 240" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
            <defs>
              <linearGradient id="meshfill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={palette.accent} stopOpacity="0.4"/>
                <stop offset="100%" stopColor={palette.accent} stopOpacity="0"/>
              </linearGradient>
            </defs>
            {[0, 0.25, 0.5, 0.75, 1].map(p => (
              <line key={p} x1="0" x2="800" y1={p * 240} y2={p * 240} stroke={palette.border} strokeWidth="1" />
            ))}
            <polyline points={`0,240 ${PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 230 - ((d.units - min) / (max - min)) * 220;
              return `${x},${y}`;
            }).join(" ")} 800,240`} fill="url(#meshfill)" />
            <polyline points={PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 230 - ((d.units - min) / (max - min)) * 220;
              return `${x},${y}`;
            }).join(" ")} fill="none" stroke={palette.accent} strokeWidth="2" />
          </svg>
        </div>
      </MeshGlassCard>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 24 }}>
        <MeshGlassCard palette={palette} padding={24}>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 20 }}>BY SPORT</div>
          {SPORT_BREAKDOWN.map(s => (
            <div key={s.sport} style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 12 }}>
                <span style={{ fontWeight: 600 }}>{s.sport}</span>
                <span style={{ color: palette.muted, fontFamily: fontMono }}>{s.picks} · <span style={{ color: palette.win }}>{s.winRate}%</span></span>
              </div>
              <div style={{ height: 6, background: palette.surface2, borderRadius: 999, position: "relative", overflow: "hidden" }}>
                <div style={{ position: "absolute", inset: 0, width: `${(s.winRate - 50) * 5}%`, background: `linear-gradient(90deg, ${palette.accent}, ${palette.win})`, borderRadius: 999 }} />
              </div>
            </div>
          ))}
        </MeshGlassCard>

        <MeshGlassCard palette={palette} padding={0}>
          <div style={{ padding: "20px 24px 12px" }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5 }}>RECENT PICKS · LAST 10</div>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ color: palette.muted, fontSize: 10, letterSpacing: 1, fontFamily: fontMono }}>
                <th style={{ padding: "10px 24px", textAlign: "left", fontWeight: 400 }}>DATE</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>MATCH</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>PICK</th>
                <th style={{ padding: "10px 24px", textAlign: "right", fontWeight: 400 }}>RES</th>
                <th style={{ padding: "10px 24px 10px 0", textAlign: "right", fontWeight: 400 }}>U</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_PICKS.map((p, i) => (
                <tr key={i} style={{ borderTop: `1px solid ${palette.border}` }}>
                  <td style={{ padding: "11px 24px", color: palette.muted, fontFamily: fontMono, fontSize: 11 }}>{p.date}</td>
                  <td style={{ padding: "11px 0" }}>{p.matchup}</td>
                  <td style={{ padding: "11px 0", fontFamily: fontMono, fontSize: 12 }}>{p.pick}</td>
                  <td style={{ padding: "11px 24px", textAlign: "right" }}>
                    <span style={{
                      display: "inline-block", padding: "2px 8px", borderRadius: 6,
                      background: p.result === "W" ? `${palette.win}22` : `${palette.loss}22`,
                      color: p.result === "W" ? palette.win : palette.loss,
                      fontFamily: fontMono, fontSize: 10, fontWeight: 700,
                    }}>{p.result}</span>
                  </td>
                  <td style={{ padding: "11px 24px 11px 0", textAlign: "right", fontFamily: fontMono, color: p.units.startsWith("+") ? palette.win : palette.loss }}>{p.units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </MeshGlassCard>
      </div>
    </div>
  );
};

// === BACKTEST ===
const MeshBacktest = ({ palette, fontDisplay, fontMono }) => (
  <div style={{ padding: "48px 32px", maxWidth: 1376, margin: "0 auto" }}>
    <div style={{ marginBottom: 40 }}>
      <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.accent, letterSpacing: 2, marginBottom: 8 }}>◆ TRANSPARENCY · 2019–2026</div>
      <h2 style={{ fontSize: 56, fontWeight: 500, margin: "0 0 14px", letterSpacing: -2 }}>Six seasons.<br/><span style={{ color: palette.muted }}>Every pick on record.</span></h2>
      <p style={{ fontSize: 16, color: palette.muted, maxWidth: 640, lineHeight: 1.5 }}>
        Out-of-sample backtests using rolling-window training. No retroactive line shopping. No selection bias.
      </p>
    </div>

    <MeshGlassCard palette={palette} padding={28} style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24, alignItems: "flex-start" }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 4 }}>CUMULATIVE UNITS · ALL SPORTS</div>
          <div style={{ fontSize: 36, fontWeight: 500, letterSpacing: -1 }}>+388.6 units</div>
        </div>
        <div style={{ display: "flex", gap: 18, fontSize: 11, color: palette.muted, fontFamily: fontMono }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 2, background: palette.accent }} /> Cumulative</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 2, background: palette.win, borderTop: `1px dashed ${palette.win}` }} /> Random baseline</div>
        </div>
      </div>
      <div style={{ height: 280 }}>
        <svg viewBox="0 0 800 280" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="btfill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={palette.accent} stopOpacity="0.35"/>
              <stop offset="100%" stopColor={palette.accent} stopOpacity="0"/>
            </linearGradient>
          </defs>
          {[0, 0.25, 0.5, 0.75, 1].map(p => (
            <line key={p} x1="0" x2="800" y1={p * 280} y2={p * 280} stroke={palette.border} strokeWidth="1" />
          ))}
          {(() => {
            const pts = [];
            let cum = 0;
            const total = 388.6;
            const segs = 90;
            const segPerSeason = segs / SEASON_BACKTEST.length;
            SEASON_BACKTEST.forEach((s, si) => {
              for (let k = 0; k < segPerSeason; k++) {
                const tt = k / segPerSeason;
                const v = cum + s.units * tt + (Math.sin(k * 0.5 + si) * 1.8);
                const xi = (si * segPerSeason + k);
                const x = (xi / segs) * 800;
                const y = 270 - (v / total) * 250;
                pts.push(`${x},${y}`);
              }
              cum += s.units;
            });
            return (
              <>
                <polyline points={`0,280 ${pts.join(" ")} 800,280`} fill="url(#btfill)" />
                <polyline points={pts.join(" ")} fill="none" stroke={palette.accent} strokeWidth="2" />
                <line x1="0" y1="265" x2="800" y2="265" stroke={palette.win} strokeWidth="1" strokeDasharray="4 4" opacity="0.6" />
              </>
            );
          })()}
        </svg>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
        {SEASON_BACKTEST.map(s => <span key={s.season}>{s.season}</span>)}
      </div>
    </MeshGlassCard>

    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
      {[
        { k: "OUT-OF-SAMPLE", v: "100%", sub: "rolling-window training; no leakage" },
        { k: "AVG SAMPLE", v: "2,193", sub: "picks per season" },
        { k: "WORST DRAWDOWN", v: "-12.4u", sub: "Q3 2021, 14-day window" },
      ].map((m, i) => (
        <MeshGlassCard key={i} palette={palette} padding={24}>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 12 }}>{m.k}</div>
          <div style={{ fontSize: 36, fontWeight: 500, letterSpacing: -1, marginBottom: 8 }}>{m.v}</div>
          <div style={{ fontSize: 12, color: palette.muted }}>{m.sub}</div>
        </MeshGlassCard>
      ))}
    </div>

    <MeshGlassCard palette={palette} padding={0}>
      <div style={{ padding: "20px 28px 12px" }}>
        <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5 }}>SEASON-BY-SEASON</div>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ color: palette.muted, fontSize: 10, letterSpacing: 1, fontFamily: fontMono }}>
            <th style={{ padding: "10px 28px", textAlign: "left", fontWeight: 400 }}>SEASON</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>PICKS</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>WIN RATE</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>UNITS</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>ROI</th>
            <th style={{ padding: "10px 28px", textAlign: "right", fontWeight: 400 }}>EQUITY</th>
          </tr>
        </thead>
        <tbody>
          {SEASON_BACKTEST.map(s => (
            <tr key={s.season} style={{ borderTop: `1px solid ${palette.border}` }}>
              <td style={{ padding: "14px 28px", fontWeight: 600 }}>{s.season}</td>
              <td style={{ padding: "14px 0", textAlign: "right", color: palette.muted, fontFamily: fontMono }}>{s.picks.toLocaleString()}</td>
              <td style={{ padding: "14px 0", textAlign: "right", fontFamily: fontMono }}>{s.winRate}%</td>
              <td style={{ padding: "14px 0", textAlign: "right", fontFamily: fontMono, color: palette.win, fontWeight: 600 }}>+{s.units}</td>
              <td style={{ padding: "14px 0", textAlign: "right", fontFamily: fontMono }}>+{s.roi}%</td>
              <td style={{ padding: "14px 28px", textAlign: "right" }}>
                <svg width="100" height="24" viewBox="0 0 100 24" style={{ verticalAlign: "middle" }}>
                  <polyline points={Array.from({ length: 16 }, (_, k) => `${(k / 15) * 100},${22 - (s.units / 80) * (k / 15) * 22 - Math.sin(k) * 0.5}`).join(" ")}
                    fill="none" stroke={palette.accent} strokeWidth="1.5" />
                </svg>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </MeshGlassCard>
  </div>
);

window.MeshApp = MeshApp;
