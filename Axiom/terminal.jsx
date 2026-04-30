// DIRECTION 1: AXIOM TERMINAL
// Quant / Wall-Street serious. IBM Plex Sans + JetBrains Mono. Dense, precise grid mesh.
// Accents: green (primary, profit/win) + blue (secondary, model/algorithm identity).

const TERMINAL_TWEAKS_DEFAULTS = /*EDITMODE-BEGIN*/{
  "greenHue": 145,
  "blueHue": 250,
  "accentChroma": 0.16,
  "meshDensity": 75,
  "showTicker": true,
  "blueAccentStrength": 60
}/*EDITMODE-END*/;

const TerminalApp = ({ width = 1440, height = 900 }) => {
  const [tab, setTab] = React.useState("home");
  const [dark, setDark] = React.useState(false);
  const [selectedPick, setSelectedPick] = React.useState(null);
  const scrollRef = React.useRef(null);

  const [tweaks, setTweak] = (window.useTweaks || (() => [TERMINAL_TWEAKS_DEFAULTS, () => {}]))(TERMINAL_TWEAKS_DEFAULTS);

  const { greenHue, blueHue, accentChroma, blueAccentStrength, showTicker } = tweaks;
  const blueWeight = blueAccentStrength / 100; // 0..1 controls how much blue shows up

  const palette = React.useMemo(() => dark ? {
    bg: "#0a0d12",
    surface: "#10141b",
    surface2: "#161b25",
    border: "rgba(255,255,255,0.08)",
    border2: "rgba(255,255,255,0.14)",
    text: "#e8edf5",
    muted: "#7c8597",
    accent: `oklch(0.72 ${accentChroma} ${greenHue})`,
    accentDim: `oklch(0.5 ${accentChroma * 0.75} ${greenHue})`,
    danger: "oklch(0.68 0.2 25)",
    blue: `oklch(0.72 ${accentChroma * 1.1} ${blueHue})`,
    blueDim: `oklch(0.5 ${accentChroma * 0.8} ${blueHue})`,
  } : {
    bg: "#fafbfc",
    surface: "#ffffff",
    surface2: "#f4f6f9",
    border: "rgba(15,20,30,0.08)",
    border2: "rgba(15,20,30,0.14)",
    text: "#0d1320",
    muted: "#5c6473",
    accent: `oklch(0.55 ${accentChroma} ${greenHue})`,
    accentDim: `oklch(0.7 ${accentChroma * 0.6} ${greenHue})`,
    danger: "oklch(0.58 0.22 25)",
    blue: `oklch(0.5 ${accentChroma * 1.1} ${blueHue})`,
    blueDim: `oklch(0.7 ${accentChroma * 0.6} ${blueHue})`,
  }, [dark, greenHue, blueHue, accentChroma]);

  const fontSans = "'IBM Plex Sans', system-ui, sans-serif";
  const fontMono = "'JetBrains Mono', ui-monospace, monospace";

  const shellStyle = {
    width, height,
    background: palette.bg,
    color: palette.text,
    fontFamily: fontSans,
    position: "relative",
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    fontSize: 13,
  };

  return (
    <div style={shellStyle}>
      {/* Ticker */}
      {showTicker && <div style={{
        height: 28, borderBottom: `1px solid ${palette.border}`,
        background: palette.surface, fontFamily: fontMono, fontSize: 11,
        display: "flex", alignItems: "center", gap: 32, padding: "0 16px",
        color: palette.muted, overflow: "hidden", whiteSpace: "nowrap",
        position: "relative", zIndex: 5,
      }}>
        <span style={{ color: palette.accent, fontWeight: 600 }}>● LIVE</span>
        <span>WIN_RATE <span style={{ color: palette.accent }}>65.1%</span></span>
        <span>30D_UNITS <span style={{ color: palette.accent }}>+18.4</span></span>
        <span>YTD_ROI <span style={{ color: palette.accent }}>+18.2%</span></span>
        <span>OPEN_PICKS <span style={{ color: palette.blue }}>8</span></span>
        <span>HIT_STREAK <span style={{ color: palette.accent }}>W6</span></span>
        <span>MODEL <span style={{ color: palette.blue }}>v4.2.1</span></span>
        <span>UPDATED <span style={{ color: palette.text }}>14:32:08 UTC</span></span>
      </div>}

      {/* Header */}
      <header style={{
        height: 56, borderBottom: `1px solid ${palette.border}`,
        background: palette.surface,
        display: "flex", alignItems: "center", padding: "0 24px", gap: 32,
        position: "relative", zIndex: 5,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M2 18 L11 4 L20 18" stroke={palette.text} strokeWidth="1.5" />
            <path d="M6 13 L16 13" stroke={palette.text} strokeWidth="1.5" />
            <circle cx="11" cy="4" r="1.6" fill={palette.accent} />
            <circle cx="2" cy="18" r="1.4" fill={palette.blue} />
            <circle cx="20" cy="18" r="1.4" fill={palette.blue} />
          </svg>
          <div style={{ fontFamily: fontMono, fontSize: 13, fontWeight: 600, letterSpacing: 1 }}>AXIOM<span style={{ color: palette.muted, fontWeight: 400 }}>/TERMINAL</span></div>
        </div>
        <nav style={{ display: "flex", gap: 4, fontFamily: fontMono, fontSize: 12 }}>
          {[
            { id: "home", label: "HOME" },
            { id: "today", label: "TODAY" },
            { id: "history", label: "HISTORY" },
            { id: "backtest", label: "BACKTEST" },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: "6px 12px",
              background: tab === t.id ? palette.surface2 : "transparent",
              border: tab === t.id ? `1px solid ${palette.border2}` : "1px solid transparent",
              color: tab === t.id ? palette.text : palette.muted,
              cursor: "pointer", fontFamily: fontMono, fontSize: 12, letterSpacing: 0.5,
            }}>{t.label}</button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted }}>SESSION_24Q2</div>
          <button onClick={() => setDark(!dark)} style={{
            width: 44, height: 22, background: palette.surface2, border: `1px solid ${palette.border2}`,
            borderRadius: 0, position: "relative", cursor: "pointer", padding: 0,
          }}>
            <div style={{
              position: "absolute", top: 1, left: dark ? 23 : 1,
              width: 18, height: 18, background: palette.accent,
              transition: "left 0.2s",
            }} />
          </button>
          <button style={{
            padding: "6px 14px", background: palette.text, color: palette.bg,
            border: "none", fontFamily: fontMono, fontSize: 11, letterSpacing: 1, cursor: "pointer",
          }}>SUBSCRIBE</button>
        </div>
      </header>

      {/* Tweaks panel */}
      {window.TweaksPanel && (
        <window.TweaksPanel title="Tweaks">
          <window.TweakSection title="Color">
            <window.TweakSlider label="Blue accent strength" value={tweaks.blueAccentStrength} min={0} max={100} step={5} onChange={(v) => setTweak("blueAccentStrength", v)} suffix="%" />
            <window.TweakSlider label="Green hue" value={tweaks.greenHue} min={120} max={170} step={1} onChange={(v) => setTweak("greenHue", v)} suffix="°" />
            <window.TweakSlider label="Blue hue" value={tweaks.blueHue} min={220} max={280} step={1} onChange={(v) => setTweak("blueHue", v)} suffix="°" />
            <window.TweakSlider label="Accent chroma" value={tweaks.accentChroma} min={0.05} max={0.25} step={0.01} onChange={(v) => setTweak("accentChroma", v)} />
          </window.TweakSection>
          <window.TweakSection title="Background">
            <window.TweakSlider label="Mesh density" value={tweaks.meshDensity} min={20} max={150} step={5} onChange={(v) => setTweak("meshDensity", v)} suffix="px" />
          </window.TweakSection>
          <window.TweakSection title="Chrome">
            <window.TweakToggle label="Show ticker" value={tweaks.showTicker} onChange={(v) => setTweak("showTicker", v)} />
          </window.TweakSection>
        </window.TweaksPanel>
      )}

      {/* Body */}
      <div ref={scrollRef} style={{ flex: 1, overflow: "auto", position: "relative" }}>
        <MeshBg variant="precise" dark={dark} scrollEl={scrollRef} accentA={palette.accent} accentB={palette.blue} density={tweaks.meshDensity} />
        <div style={{ position: "relative", zIndex: 1 }}>
          {tab === "home" && <TerminalHome palette={palette} fontMono={fontMono} fontSans={fontSans} blueWeight={blueWeight} />}
          {tab === "today" && <TerminalToday palette={palette} fontMono={fontMono} fontSans={fontSans} selectedPick={selectedPick} setSelectedPick={setSelectedPick} blueWeight={blueWeight} />}
          {tab === "history" && <TerminalHistory palette={palette} fontMono={fontMono} fontSans={fontSans} blueWeight={blueWeight} />}
          {tab === "backtest" && <TerminalBacktest palette={palette} fontMono={fontMono} fontSans={fontSans} blueWeight={blueWeight} />}
        </div>
      </div>
    </div>
  );
};

// === HOME ===
const TerminalHome = ({ palette, fontMono, fontSans, blueWeight = 0.6 }) => (

  <div style={{ padding: "48px 32px 80px" }}>
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 2, marginBottom: 16 }}>
        ◆ QUANTITATIVE SPORTS INTELLIGENCE / EST. 2019
      </div>
      <h1 style={{
        fontSize: 72, lineHeight: 0.95, fontWeight: 500, letterSpacing: -2,
        margin: "0 0 28px", maxWidth: 920, fontFamily: fontSans,
      }}>
        The market is wrong<br/>
        <span style={{ color: palette.muted }}>3.2 times per day.</span>
      </h1>
      <p style={{ fontSize: 17, lineHeight: 1.5, color: palette.muted, maxWidth: 600, margin: "0 0 40px" }}>
        Axiom is a quantitative model that ingests 14M data points across seven leagues to identify mispriced lines. Output: high-conviction picks with documented edge.
      </p>

      {/* Hero metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 1, background: palette.border, border: `1px solid ${palette.border}`, marginBottom: 56 }}>
        {[
          { k: "WIN RATE", v: "65%", sub: "across 10,243 picks", trend: "+0.4%", color: palette.accent },
          { k: "UNITS", v: "+71.0", sub: "season to date", trend: "+18.4 30D", color: palette.accent },
          { k: "PICKS TRACKED", v: "10,243", sub: "since Sept 2019", trend: "100% public log", color: palette.blue },
        ].map((m, i) => (
          <div key={i} style={{ background: palette.surface, padding: "32px 28px", position: "relative" }}>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 12 }}>{m.k}</div>
            <div style={{ fontSize: 56, fontWeight: 500, fontFamily: fontMono, lineHeight: 1, marginBottom: 8, letterSpacing: -1 }}>{m.v}</div>
            <div style={{ fontSize: 12, color: palette.muted, fontFamily: fontMono }}>{m.sub}</div>
            <div style={{ position: "absolute", top: 28, right: 28, fontFamily: fontMono, fontSize: 11, color: m.color, padding: "2px 6px", border: `1px solid ${m.color}` }}>{m.trend}</div>
          </div>
        ))}
      </div>

      {/* Two col */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, marginBottom: 56 }}>
        <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 32 }}>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 20 }}>02 / METHODOLOGY</div>
          <div style={{ fontSize: 22, fontWeight: 500, lineHeight: 1.3, marginBottom: 20, letterSpacing: -0.3 }}>
            <span style={{ color: palette.blue }}>Bayesian ensemble</span> across 47 input features.
          </div>
          <p style={{ color: palette.muted, lineHeight: 1.55, fontSize: 13, marginBottom: 16 }}>
            We model line movement, public money distribution, weather, rest days, travel, lineup volatility, referee tendencies, and 41 other signals. The output is a closing-line probability we can compare against the book.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontFamily: fontMono, fontSize: 11 }}>
            {["BAYES_ENSEMBLE", "MONTE_CARLO_2K", "KELLY_SIZING", "CLV_TRACKED"].map((t, i) => (
              <div key={t} style={{ padding: "6px 10px", background: palette.surface2, color: palette.muted, letterSpacing: 1, borderLeft: `2px solid ${i % 2 ? palette.blue : palette.accent}` }}>{i % 2 ? "◆" : "●"} {t}</div>
            ))}
          </div>
        </div>
        <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 32 }}>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 20 }}>03 / TRANSPARENCY</div>
          <div style={{ fontSize: 22, fontWeight: 500, lineHeight: 1.3, marginBottom: 20, letterSpacing: -0.3 }}>
            Every pick logged. Wins and losses.
          </div>
          {/* mini sparkline */}
          <div style={{ height: 80, marginBottom: 16, position: "relative" }}>
            <svg viewBox="0 0 400 80" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
              <defs>
                <linearGradient id="home-spark" x1="0" x2="1" y1="0" y2="0">
                  <stop offset="0%" stopColor={palette.blue}/>
                  <stop offset="100%" stopColor={palette.accent}/>
                </linearGradient>
              </defs>
              <polyline points={PERFORMANCE_30D.map((d, i) => `${(i / 29) * 400},${75 - (d.units / 25) * 65}`).join(" ")}
                fill="none" stroke="url(#home-spark)" strokeWidth="1.5" />
              <polyline points={`0,75 ${PERFORMANCE_30D.map((d, i) => `${(i / 29) * 400},${75 - (d.units / 25) * 65}`).join(" ")} 400,75`}
                fill={palette.accent} opacity="0.1" />
            </svg>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: fontMono, fontSize: 11, color: palette.muted }}>
            <span>30D PERFORMANCE</span>
            <span style={{ color: palette.accent }}>+18.4 UNITS</span>
          </div>
        </div>
      </div>

      {/* Latest picks teaser */}
      <div style={{ marginBottom: 24, display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5 }}>04 / TODAY'S BOARD <span style={{ color: palette.accent, marginLeft: 12 }}>● 8 LIVE PICKS</span></div>
        <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted }}>VIEW ALL →</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {TODAYS_GAMES.slice(0, 4).map((g, i) => (
          <TerminalGameCard key={i} g={g} palette={palette} fontMono={fontMono} />
        ))}
      </div>
    </div>
  </div>
);

// Glass game card with soft glow
const TerminalGameCard = ({ g, palette, fontMono, onClick }) => (
  <div onClick={onClick} style={{
    background: palette.surface,
    border: `1px solid ${palette.border}`,
    padding: 16,
    position: "relative",
    cursor: onClick ? "pointer" : "default",
    backdropFilter: "blur(10px)",
    boxShadow: `0 0 0 1px ${palette.border}, 0 8px 24px -12px ${palette.accent}33`,
  }}>
    <div style={{ position: "absolute", inset: -1, background: `radial-gradient(circle at 50% -20%, ${palette.accent}22, transparent 60%)`, pointerEvents: "none" }} />
    <div style={{ position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1, marginBottom: 14 }}>
        <span>{g.league}</span>
        <span>{g.time}</span>
      </div>
      <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>{g.awayAbbr} @ {g.homeAbbr}</div>
      <div style={{ fontSize: 11, color: palette.muted, marginBottom: 16, fontFamily: fontMono }}>{g.away} · {g.home}</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1, marginBottom: 4 }}>PICK</div>
          <div style={{ fontFamily: fontMono, fontSize: 15, color: palette.accent, fontWeight: 600 }}>{g.pick}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1, marginBottom: 4 }}>EDGE</div>
          <div style={{ fontFamily: fontMono, fontSize: 15, fontWeight: 600 }}>{g.edge}</div>
        </div>
      </div>
      {/* confidence bar */}
      <div style={{ marginTop: 14, height: 2, background: palette.surface2, position: "relative" }}>
        <div style={{ position: "absolute", inset: 0, width: `${g.confidence}%`, background: palette.accent }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 1 }}>
        <span>CONF</span>
        <span>{g.confidence}%</span>
      </div>
    </div>
  </div>
);

// === TODAY ===
const TerminalToday = ({ palette, fontMono, fontSans, selectedPick, setSelectedPick, blueWeight = 0.6 }) => {
  const games = TODAYS_GAMES;
  return (
    <div style={{ padding: "32px", display: "grid", gridTemplateColumns: selectedPick ? "1fr 420px" : "1fr", gap: 24, maxWidth: 1376, margin: "0 auto" }}>
      <div>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 6 }}>04.28.2026 / TUESDAY</div>
            <h2 style={{ fontSize: 36, fontWeight: 500, margin: 0, letterSpacing: -1 }}>Today's Board</h2>
          </div>
          <div style={{ display: "flex", gap: 8, fontFamily: fontMono, fontSize: 11 }}>
            {["ALL", "NBA", "NFL", "MLB", "NHL", "NCAA", "EPL"].map((t, i) => (
              <div key={t} style={{
                padding: "6px 12px", background: i === 0 ? palette.text : palette.surface,
                color: i === 0 ? palette.bg : palette.muted, border: `1px solid ${palette.border2}`, cursor: "pointer", letterSpacing: 1,
              }}>{t}</div>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: selectedPick ? "repeat(2, 1fr)" : "repeat(4, 1fr)", gap: 12 }}>
          {games.map((g, i) => (
            <TerminalGameCard key={i} g={g} palette={palette} fontMono={fontMono} onClick={() => setSelectedPick(g)} />
          ))}
        </div>
      </div>

      {selectedPick && (
        <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 24, height: "fit-content", position: "sticky", top: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5 }}>PICK DETAIL</div>
            <button onClick={() => setSelectedPick(null)} style={{ background: "transparent", border: "none", color: palette.muted, cursor: "pointer", fontSize: 18, lineHeight: 1 }}>×</button>
          </div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1, marginBottom: 8 }}>{selectedPick.league} / {selectedPick.time}</div>
          <div style={{ fontSize: 26, fontWeight: 500, marginBottom: 4, letterSpacing: -0.5 }}>{selectedPick.away}</div>
          <div style={{ fontSize: 13, color: palette.muted, fontFamily: fontMono, marginBottom: 8 }}>@</div>
          <div style={{ fontSize: 26, fontWeight: 500, marginBottom: 24, letterSpacing: -0.5 }}>{selectedPick.home}</div>

          <div style={{ background: palette.surface2, border: `1px solid ${palette.border}`, borderLeft: `2px solid ${palette.blue}`, padding: 20, marginBottom: 20 }}>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.blue, letterSpacing: 1, marginBottom: 8 }}>◆ RECOMMENDATION</div>
            <div style={{ fontSize: 32, fontFamily: fontMono, color: palette.accent, fontWeight: 600, marginBottom: 4 }}>{selectedPick.pick}</div>
            <div style={{ display: "flex", gap: 24, marginTop: 16 }}>
              <div><div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>UNITS</div><div style={{ fontFamily: fontMono, fontSize: 16, fontWeight: 600 }}>{selectedPick.units}u</div></div>
              <div><div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>EDGE</div><div style={{ fontFamily: fontMono, fontSize: 16, fontWeight: 600 }}>{selectedPick.edge}</div></div>
              <div><div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>CONF</div><div style={{ fontFamily: fontMono, fontSize: 16, fontWeight: 600 }}>{selectedPick.confidence}%</div></div>
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1, marginBottom: 12 }}>MODEL SIGNAL BREAKDOWN</div>
            {[
              { k: "Pace differential", v: 78, color: palette.accent },
              { k: "Rest advantage", v: 64, color: palette.blue },
              { k: "Line vs. closing", v: 82, color: palette.accent },
              { k: "Travel impact", v: 41, color: palette.blue },
              { k: "Lineup confidence", v: 91, color: palette.accent },
            ].map(s => (
              <div key={s.k} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: fontMono, marginBottom: 4 }}>
                  <span style={{ color: palette.muted }}>{s.k}</span>
                  <span>{s.v}</span>
                </div>
                <div style={{ height: 2, background: palette.surface2, position: "relative" }}>
                  <div style={{ position: "absolute", inset: 0, width: `${s.v}%`, background: s.color }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: palette.surface2, padding: 16, fontFamily: fontMono, fontSize: 11, lineHeight: 1.5, color: palette.muted, borderLeft: `2px solid ${palette.blue}` }}>
            // ANALYST_NOTE<br/>
            Closing line value detected at -3.5; market drifting toward -2.5. Pace mismatch favors {selectedPick.homeAbbr} in transition. Confidence elevated post lineup confirmation 14:08 UTC.
          </div>
        </div>
      )}
    </div>
  );
};

// === HISTORY ===
const TerminalHistory = ({ palette, fontMono, fontSans, blueWeight = 0.6 }) => {
  const max = Math.max(...PERFORMANCE_30D.map(d => d.units));
  const min = Math.min(0, ...PERFORMANCE_30D.map(d => d.units));
  return (
    <div style={{ padding: "32px", maxWidth: 1376, margin: "0 auto" }}>
      <div style={{ marginBottom: 24, display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 6 }}>PERFORMANCE / ROLLING 30D</div>
          <h2 style={{ fontSize: 36, fontWeight: 500, margin: 0, letterSpacing: -1 }}>Model History</h2>
        </div>
        <div style={{ display: "flex", gap: 8, fontFamily: fontMono, fontSize: 11 }}>
          {["7D", "30D", "90D", "YTD", "ALL"].map((t, i) => (
            <div key={t} style={{
              padding: "6px 12px", background: i === 1 ? palette.text : palette.surface,
              color: i === 1 ? palette.bg : palette.muted, border: `1px solid ${palette.border2}`, cursor: "pointer", letterSpacing: 1,
            }}>{t}</div>
          ))}
        </div>
      </div>

      {/* KPI strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 1, background: palette.border, border: `1px solid ${palette.border}`, marginBottom: 24 }}>
        {[
          { k: "WIN RATE", v: "65.4%", d: "+1.1pp", color: palette.accent },
          { k: "PICKS", v: "187", d: "30D", color: palette.blue },
          { k: "UNITS", v: "+18.4", d: "+24%", color: palette.accent },
          { k: "ROI", v: "+19.6%", d: "+2.3pp", color: palette.accent },
          { k: "AVG EDGE", v: "3.7%", d: "+0.2pp", color: palette.blue },
        ].map((m, i) => (
          <div key={i} style={{ background: palette.surface, padding: 20 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 8 }}>{m.k}</div>
            <div style={{ fontSize: 28, fontWeight: 500, fontFamily: fontMono, letterSpacing: -0.5 }}>{m.v}</div>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: m.color, marginTop: 4 }}>↑ {m.d}</div>
          </div>
        ))}
      </div>

      {/* Big chart */}
      <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 24, marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 4 }}>CUMULATIVE UNITS / 30D</div>
            <div style={{ fontSize: 22, fontWeight: 500, fontFamily: fontMono }}>+{PERFORMANCE_30D[PERFORMANCE_30D.length - 1].units.toFixed(2)}</div>
          </div>
        </div>
        <div style={{ height: 280, position: "relative" }}>
          <svg viewBox="0 0 800 280" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
            <defs>
              <linearGradient id="hist-line" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stopColor={palette.blue}/>
                <stop offset="100%" stopColor={palette.accent}/>
              </linearGradient>
            </defs>
            {/* gridlines */}
            {[0, 0.25, 0.5, 0.75, 1].map(p => (
              <line key={p} x1="0" x2="800" y1={p * 280} y2={p * 280} stroke={palette.border} strokeWidth="1" />
            ))}
            <polyline points={PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 270 - ((d.units - min) / (max - min)) * 260;
              return `${x},${y}`;
            }).join(" ")} fill="none" stroke="url(#hist-line)" strokeWidth="1.5" />
            <polyline points={`0,280 ${PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 270 - ((d.units - min) / (max - min)) * 260;
              return `${x},${y}`;
            }).join(" ")} 800,280`} fill={palette.accent} opacity="0.08" />
            {PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 270 - ((d.units - min) / (max - min)) * 260;
              return <circle key={i} cx={x} cy={y} r="2" fill={palette.surface} stroke={i % 4 === 0 ? palette.blue : palette.accent} strokeWidth="1" />;
            })}
          </svg>
          {/* y axis labels */}
          <div style={{ position: "absolute", left: -32, top: 0, height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", fontFamily: fontMono, fontSize: 10, color: palette.muted }}>
            <span>+20u</span><span>+10u</span><span>0u</span>
          </div>
        </div>
      </div>

      {/* Two col: sport breakdown + recent picks log */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 24 }}>
        <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 24 }}>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 20 }}>BY SPORT / ALL-TIME</div>
          {SPORT_BREAKDOWN.map(s => (
            <div key={s.sport} style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontFamily: fontMono, fontSize: 12 }}>
                <span style={{ fontWeight: 600 }}>{s.sport}</span>
                <span style={{ color: palette.muted }}>{s.picks} picks · <span style={{ color: palette.accent }}>{s.winRate}%</span></span>
              </div>
              <div style={{ height: 4, background: palette.surface2, position: "relative" }}>
                <div style={{ position: "absolute", inset: 0, width: `${(s.winRate - 50) * 5}%`, background: palette.accent }} />
              </div>
            </div>
          ))}
        </div>

        <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 0 }}>
          <div style={{ padding: "20px 24px 12px", borderBottom: `1px solid ${palette.border}` }}>
            <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5 }}>PICK LOG / 10 MOST RECENT</div>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: fontMono, fontSize: 12 }}>
            <thead>
              <tr style={{ color: palette.muted, fontSize: 10, letterSpacing: 1 }}>
                <th style={{ padding: "10px 24px", textAlign: "left", fontWeight: 400 }}>DATE</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>LEAGUE</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>MATCH</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>PICK</th>
                <th style={{ padding: "10px 24px", textAlign: "right", fontWeight: 400 }}>RES</th>
                <th style={{ padding: "10px 24px 10px 0", textAlign: "right", fontWeight: 400 }}>U</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_PICKS.map((p, i) => (
                <tr key={i} style={{ borderTop: `1px solid ${palette.border}` }}>
                  <td style={{ padding: "10px 24px", color: palette.muted }}>{p.date}</td>
                  <td style={{ padding: "10px 0", color: palette.muted }}>{p.league}</td>
                  <td style={{ padding: "10px 0" }}>{p.matchup}</td>
                  <td style={{ padding: "10px 0", color: palette.text }}>{p.pick}</td>
                  <td style={{ padding: "10px 24px", textAlign: "right", color: p.result === "W" ? palette.accent : palette.danger, fontWeight: 600 }}>{p.result}</td>
                  <td style={{ padding: "10px 24px 10px 0", textAlign: "right", color: p.units.startsWith("+") ? palette.accent : palette.danger }}>{p.units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// === BACKTEST ===
const TerminalBacktest = ({ palette, fontMono, fontSans, blueWeight = 0.6 }) => (
  <div style={{ padding: "32px", maxWidth: 1376, margin: "0 auto" }}>
    <div style={{ marginBottom: 32 }}>
      <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 6 }}>HISTORICAL BACKTEST / SEASON-BY-SEASON</div>
      <h2 style={{ fontSize: 36, fontWeight: 500, margin: "0 0 12px", letterSpacing: -1 }}>Six seasons. <span style={{ color: palette.muted }}>Every pick logged.</span></h2>
      <p style={{ fontSize: 14, color: palette.muted, maxWidth: 640, lineHeight: 1.5 }}>
        Backtests use closing line value as the input price; live picks use posted line at time of release. Both are tracked separately and shown below.
      </p>
    </div>

    {/* big seasons grid */}
    <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, marginBottom: 24, overflow: "hidden" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", borderBottom: `1px solid ${palette.border}`, fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
        <div style={{ padding: "12px 20px" }}>SEASON</div>
        <div style={{ padding: "12px 20px" }}>PICKS</div>
        <div style={{ padding: "12px 20px" }}>WIN RATE</div>
        <div style={{ padding: "12px 20px" }}>UNITS</div>
        <div style={{ padding: "12px 20px" }}>ROI</div>
        <div style={{ padding: "12px 20px" }}>EQUITY CURVE</div>
      </div>
      {SEASON_BACKTEST.map((s, i) => (
        <div key={s.season} style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", borderBottom: i < 5 ? `1px solid ${palette.border}` : "none", fontFamily: fontMono, fontSize: 14 }}>
          <div style={{ padding: "20px", fontWeight: 600 }}>{s.season}</div>
          <div style={{ padding: "20px", color: palette.muted }}>{s.picks.toLocaleString()}</div>
          <div style={{ padding: "20px" }}>{s.winRate}%</div>
          <div style={{ padding: "20px", color: palette.accent }}>+{s.units}</div>
          <div style={{ padding: "20px" }}>+{s.roi}%</div>
          <div style={{ padding: "20px", display: "flex", alignItems: "center" }}>
            <svg width="120" height="32" viewBox="0 0 120 32">
              {(() => {
                const pts = Array.from({ length: 20 }, (_, k) => {
                  const x = (k / 19) * 120;
                  const v = (s.units / 80) * (k / 19) + (Math.sin(k * 1.7 + i) * 0.05);
                  const y = 28 - v * 24;
                  return `${x},${Math.max(2, Math.min(30, y))}`;
                });
                return <polyline points={pts.join(" ")} fill="none" stroke={palette.accent} strokeWidth="1.5" />;
              })()}
            </svg>
          </div>
        </div>
      ))}
    </div>

    {/* big composite chart */}
    <div style={{ background: palette.surface, border: `1px solid ${palette.border}`, padding: 24, marginBottom: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 1.5, marginBottom: 4 }}>CUMULATIVE UNITS / 2019–2026</div>
        <div style={{ fontSize: 22, fontWeight: 500, fontFamily: fontMono }}>+388.6 units across all sports</div>
      </div>
      <div style={{ height: 220 }}>
        <svg viewBox="0 0 800 220" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
          {[0, 0.25, 0.5, 0.75, 1].map(p => (
            <line key={p} x1="0" x2="800" y1={p * 220} y2={p * 220} stroke={palette.border} strokeWidth="1" />
          ))}
          {(() => {
            const pts = [];
            let cum = 0;
            const total = SEASON_BACKTEST.reduce((a, s) => a + s.units, 0);
            const segs = 80;
            SEASON_BACKTEST.forEach((s, si) => {
              for (let k = 0; k < segs / SEASON_BACKTEST.length; k++) {
                const tt = k / (segs / SEASON_BACKTEST.length);
                const v = cum + s.units * tt + (Math.sin(k * 0.6 + si) * 1.5);
                const xi = (si * (segs / SEASON_BACKTEST.length) + k);
                const x = (xi / segs) * 800;
                const y = 210 - (v / total) * 200;
                pts.push(`${x},${y}`);
              }
              cum += s.units;
            });
            return (
              <>
                <polyline points={`0,220 ${pts.join(" ")} 800,220`} fill={palette.accent} opacity="0.08" />
                <polyline points={pts.join(" ")} fill="none" stroke={palette.accent} strokeWidth="1.5" />
                {SEASON_BACKTEST.map((s, si) => {
                  const x = ((si + 1) * (segs / SEASON_BACKTEST.length) / segs) * 800 - 1;
                  return <line key={si} x1={x} x2={x} y1="0" y2="220" stroke={palette.border2} strokeDasharray="2 4" />;
                })}
              </>
            );
          })()}
        </svg>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
        {SEASON_BACKTEST.map(s => <span key={s.season}>{s.season.split("-")[0]}</span>)}
      </div>
    </div>

    {/* methodology callout */}
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1, background: palette.border, border: `1px solid ${palette.border}` }}>
      {[
        { k: "OUT-OF-SAMPLE", v: "100%", sub: "no data leakage; rolling-window training" },
        { k: "AVG SAMPLE", v: "2,193", sub: "picks per season" },
        { k: "WORST DD", v: "-12.4u", sub: "Q3 2021, 14-day window" },
      ].map((m, i) => (
        <div key={i} style={{ background: palette.surface, padding: 24 }}>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1.5, marginBottom: 10 }}>{m.k}</div>
          <div style={{ fontSize: 30, fontWeight: 500, fontFamily: fontMono, letterSpacing: -0.5, marginBottom: 6 }}>{m.v}</div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted }}>{m.sub}</div>
        </div>
      ))}
    </div>
  </div>
);

window.TerminalApp = TerminalApp;
