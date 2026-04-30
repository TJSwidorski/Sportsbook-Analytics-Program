// DIRECTION 3: AXIOM ATLAS
// Sleek luxury sportsbook. Fraunces (display serif) + Inter. Generous whitespace,
// pearlescent gradients, restrained mesh, editorial feel.

const AtlasApp = ({ width = 1440, height = 900 }) => {
  const [tab, setTab] = React.useState("home");
  const [dark, setDark] = React.useState(false);
  const [selectedPick, setSelectedPick] = React.useState(null);
  const scrollRef = React.useRef(null);

  const palette = dark ? {
    bg: "#13110e",
    surface: "rgba(30,26,22,0.6)",
    surface2: "rgba(40,34,28,0.7)",
    border: "rgba(220,210,180,0.16)",
    border2: "rgba(220,210,180,0.28)",
    text: "#f4ede0",
    muted: "#a89e8a",
    accent: "oklch(0.78 0.1 80)",
    gold: "oklch(0.82 0.12 85)",
    win: "oklch(0.7 0.15 145)",
    loss: "oklch(0.62 0.18 25)",
  } : {
    bg: "#fbf8f2",
    surface: "rgba(255,253,248,0.65)",
    surface2: "rgba(248,243,232,0.85)",
    border: "rgba(80,70,55,0.14)",
    border2: "rgba(80,70,55,0.24)",
    text: "#1a1612",
    muted: "#6b6354",
    accent: "oklch(0.55 0.12 80)",
    gold: "oklch(0.62 0.14 80)",
    win: "oklch(0.5 0.14 145)",
    loss: "oklch(0.55 0.2 25)",
  };

  const fontDisplay = "'Fraunces', Georgia, serif";
  const fontSans = "'Inter', system-ui, sans-serif";
  const fontMono = "'JetBrains Mono', ui-monospace, monospace";

  return (
    <div style={{
      width, height, background: palette.bg, color: palette.text,
      fontFamily: fontSans, position: "relative", overflow: "hidden",
      display: "flex", flexDirection: "column", fontSize: 14,
    }}>
      <header style={{
        height: 76, padding: "0 40px", display: "flex", alignItems: "center", gap: 48,
        position: "relative", zIndex: 5,
        background: dark ? "rgba(19,17,14,0.6)" : "rgba(251,248,242,0.6)",
        backdropFilter: "blur(16px)",
        borderBottom: `1px solid ${palette.border}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <svg width="28" height="28" viewBox="0 0 28 28">
            <circle cx="14" cy="14" r="12" fill="none" stroke={palette.text} strokeWidth="0.7" />
            <circle cx="14" cy="14" r="7" fill="none" stroke={palette.accent} strokeWidth="0.7" />
            <circle cx="14" cy="14" r="2" fill={palette.accent} />
            <line x1="14" y1="2" x2="14" y2="26" stroke={palette.text} strokeWidth="0.5" />
            <line x1="2" y1="14" x2="26" y2="14" stroke={palette.text} strokeWidth="0.5" />
          </svg>
          <div style={{ fontFamily: fontDisplay, fontSize: 22, fontWeight: 500, letterSpacing: -0.3, fontStyle: "italic" }}>Axiom</div>
        </div>
        <nav style={{ display: "flex", gap: 8 }}>
          {[
            { id: "home", label: "House" },
            { id: "today", label: "Today" },
            { id: "history", label: "Performance" },
            { id: "backtest", label: "Provenance" },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: "10px 18px",
              background: "transparent",
              border: "none",
              color: tab === t.id ? palette.text : palette.muted,
              cursor: "pointer", fontSize: 13, fontFamily: fontSans,
              fontWeight: tab === t.id ? 600 : 400,
              borderBottom: tab === t.id ? `2px solid ${palette.accent}` : "2px solid transparent",
              borderRadius: 0, paddingBottom: 8,
            }}>{t.label}</button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 16 }}>
          <button onClick={() => setDark(!dark)} style={{
            width: 44, height: 22, borderRadius: 999, background: palette.surface2,
            border: `1px solid ${palette.border2}`, position: "relative", cursor: "pointer", padding: 0,
          }}>
            <div style={{
              position: "absolute", top: 1, left: dark ? 22 : 1,
              width: 18, height: 18, borderRadius: "50%",
              background: palette.gold, transition: "left 0.2s",
            }} />
          </button>
          <button style={{
            padding: "10px 22px", borderRadius: 999, background: palette.text, color: palette.bg,
            fontSize: 13, fontWeight: 500, border: "none", cursor: "pointer", fontFamily: fontSans,
          }}>Become a member</button>
        </div>
      </header>

      <div ref={scrollRef} style={{ flex: 1, overflow: "auto", position: "relative" }}>
        <MeshBg variant="luxe" dark={dark} scrollEl={scrollRef} accentA={palette.gold} accentB={palette.win} />
        <div style={{ position: "relative", zIndex: 1 }}>
          {tab === "home" && <AtlasHome palette={palette} fontDisplay={fontDisplay} fontSans={fontSans} fontMono={fontMono} setTab={setTab} />}
          {tab === "today" && <AtlasToday palette={palette} fontDisplay={fontDisplay} fontSans={fontSans} fontMono={fontMono} selectedPick={selectedPick} setSelectedPick={setSelectedPick} />}
          {tab === "history" && <AtlasHistory palette={palette} fontDisplay={fontDisplay} fontSans={fontSans} fontMono={fontMono} />}
          {tab === "backtest" && <AtlasBacktest palette={palette} fontDisplay={fontDisplay} fontSans={fontSans} fontMono={fontMono} />}
        </div>
      </div>
    </div>
  );
};

const AtlasGlass = ({ children, palette, padding = 28, onClick, style = {} }) => (
  <div onClick={onClick} style={{
    background: palette.surface,
    border: `1px solid ${palette.border}`,
    borderRadius: 22,
    padding,
    position: "relative",
    backdropFilter: "blur(20px)",
    cursor: onClick ? "pointer" : "default",
    boxShadow: `0 1px 0 rgba(255,255,255,0.4) inset, 0 24px 60px -32px rgba(80,70,55,0.25)`,
    overflow: "hidden",
    ...style,
  }}>
    <div style={{
      position: "absolute", inset: -1, borderRadius: 22,
      background: `radial-gradient(ellipse 80% 60% at 50% -10%, ${palette.gold}22, transparent 70%)`,
      pointerEvents: "none",
    }} />
    <div style={{ position: "relative" }}>{children}</div>
  </div>
);

// === HOME ===
const AtlasHome = ({ palette, fontDisplay, fontSans, fontMono, setTab }) => (
  <div style={{ padding: "80px 40px 96px" }}>
    <div style={{ maxWidth: 1080, margin: "0 auto" }}>
      <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.muted, letterSpacing: 3, textTransform: "uppercase", marginBottom: 28 }}>
        Quantitative Sports Intelligence — Est. 2019
      </div>
      <h1 style={{
        fontFamily: fontDisplay, fontSize: 108, lineHeight: 0.95, fontWeight: 400,
        letterSpacing: -3.5, margin: "0 0 32px", maxWidth: 1000,
      }}>
        Where the<br/>
        <em style={{ fontWeight: 400, color: palette.accent }}>line breaks.</em>
      </h1>
      <p style={{ fontSize: 19, lineHeight: 1.5, color: palette.muted, maxWidth: 560, margin: "0 0 64px", fontWeight: 400 }}>
        A quiet, six-year quantitative model that finds the few moments each day when the market is wrong. We publish every pick. Wins, losses, and everything in between.
      </p>

      {/* hero metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, marginBottom: 96 }}>
        {[
          { k: "Win rate", v: "65%", sub: "across 10,243 published picks" },
          { k: "Up units", v: "+71", sub: "season to date, +18.4 this month" },
          { k: "Picks tracked", v: "10K+", sub: "every one logged since 2019" },
        ].map((m, i) => (
          <AtlasGlass key={i} palette={palette} padding={32}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 20 }}>0{i + 1} · {m.k}</div>
            <div style={{ fontFamily: fontDisplay, fontSize: 84, fontWeight: 400, lineHeight: 0.9, letterSpacing: -3, marginBottom: 16, fontStyle: i === 1 ? "italic" : "normal" }}>{m.v}</div>
            <div style={{ fontSize: 13, color: palette.muted, lineHeight: 1.5 }}>{m.sub}</div>
          </AtlasGlass>
        ))}
      </div>

      {/* editorial: methodology */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, marginBottom: 96 }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.gold, letterSpacing: 3, textTransform: "uppercase", marginBottom: 20 }}>Methodology</div>
          <h2 style={{ fontFamily: fontDisplay, fontSize: 48, lineHeight: 1.05, fontWeight: 400, margin: "0 0 24px", letterSpacing: -1.5 }}>
            Forty-seven inputs. <em>One conviction.</em>
          </h2>
          <p style={{ fontSize: 15, lineHeight: 1.65, color: palette.muted, marginBottom: 16 }}>
            We model line movement, public money distribution, weather, rest days, travel, lineup volatility, referee tendencies, and 41 other signals. The model produces a closing-line probability we compare against the book.
          </p>
          <p style={{ fontSize: 15, lineHeight: 1.65, color: palette.muted, marginBottom: 24 }}>
            When the gap is wide enough — and only then — we publish a pick.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, paddingTop: 24, borderTop: `1px solid ${palette.border}` }}>
            <div>
              <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>EDGE THRESHOLD</div>
              <div style={{ fontFamily: fontDisplay, fontSize: 24, fontWeight: 400 }}>≥ 2.5%</div>
            </div>
            <div>
              <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>STAKE METHOD</div>
              <div style={{ fontFamily: fontDisplay, fontSize: 24, fontWeight: 400 }}>Half-Kelly</div>
            </div>
            <div>
              <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>UPDATE WINDOW</div>
              <div style={{ fontFamily: fontDisplay, fontSize: 24, fontWeight: 400 }}>Every 4 min</div>
            </div>
            <div>
              <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>LEAGUES</div>
              <div style={{ fontFamily: fontDisplay, fontSize: 24, fontWeight: 400 }}>Seven</div>
            </div>
          </div>
        </div>
        <AtlasGlass palette={palette} padding={32}>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.gold, letterSpacing: 3, textTransform: "uppercase", marginBottom: 20 }}>30-day equity</div>
          <div style={{ fontFamily: fontDisplay, fontSize: 56, fontWeight: 400, letterSpacing: -1.5, marginBottom: 6 }}>+18.4 <span style={{ fontSize: 18, color: palette.muted, fontStyle: "italic" }}>units</span></div>
          <div style={{ fontSize: 13, color: palette.muted, marginBottom: 28 }}>↑ 24% from prior 30 days</div>
          <div style={{ height: 200 }}>
            <svg viewBox="0 0 400 200" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
              <defs>
                <linearGradient id="atlfill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor={palette.accent} stopOpacity="0.25"/>
                  <stop offset="100%" stopColor={palette.accent} stopOpacity="0"/>
                </linearGradient>
              </defs>
              {(() => {
                const max = Math.max(...PERFORMANCE_30D.map(d => d.units));
                const pts = PERFORMANCE_30D.map((d, i) => `${(i / 29) * 400},${190 - (d.units / max) * 170}`).join(" ");
                return <>
                  <polyline points={`0,200 ${pts} 400,200`} fill="url(#atlfill)" />
                  <polyline points={pts} fill="none" stroke={palette.accent} strokeWidth="1.5" />
                </>;
              })()}
            </svg>
          </div>
        </AtlasGlass>
      </div>

      {/* today's picks teaser */}
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 28 }}>
        <h2 style={{ fontFamily: fontDisplay, fontSize: 36, fontWeight: 400, margin: 0, letterSpacing: -1 }}>Today's selections</h2>
        <button onClick={() => setTab("today")} style={{ background: "transparent", border: "none", color: palette.text, fontSize: 13, cursor: "pointer", fontFamily: fontSans }}>View all eight →</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20 }}>
        {TODAYS_GAMES.slice(0, 4).map((g, i) => (
          <AtlasGameCard key={i} g={g} palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} onClick={() => setTab("today")} />
        ))}
      </div>
    </div>
  </div>
);

const AtlasGameCard = ({ g, palette, fontDisplay, fontMono, onClick }) => (
  <AtlasGlass palette={palette} padding={22} onClick={onClick}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
      <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2 }}>{g.league}</div>
      <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted }}>{g.time}</div>
    </div>
    <div style={{ fontFamily: fontDisplay, fontSize: 22, fontWeight: 400, lineHeight: 1.2, marginBottom: 4, letterSpacing: -0.5 }}>{g.awayAbbr} <span style={{ color: palette.muted, fontStyle: "italic", fontSize: 16 }}>at</span> {g.homeAbbr}</div>
    <div style={{ fontSize: 11, color: palette.muted, marginBottom: 20, lineHeight: 1.4 }}>{g.away} · {g.home}</div>
    <div style={{ paddingTop: 18, borderTop: `1px solid ${palette.border}`, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
      <div>
        <div style={{ fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>SELECTION</div>
        <div style={{ fontFamily: fontDisplay, fontSize: 18, fontWeight: 500, color: palette.accent, letterSpacing: -0.3 }}>{g.pick}</div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>EDGE</div>
        <div style={{ fontFamily: fontDisplay, fontSize: 18, fontWeight: 500 }}>{g.edge}</div>
      </div>
    </div>
  </AtlasGlass>
);

// === TODAY ===
const AtlasToday = ({ palette, fontDisplay, fontSans, fontMono, selectedPick, setSelectedPick }) => (
  <div style={{ padding: "56px 40px", maxWidth: 1376, margin: "0 auto", display: "grid", gridTemplateColumns: selectedPick ? "1fr 460px" : "1fr", gap: 32 }}>
    <div>
      <div style={{ marginBottom: 36 }}>
        <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.gold, letterSpacing: 3, textTransform: "uppercase", marginBottom: 10 }}>Tuesday · April 28, 2026</div>
        <h2 style={{ fontFamily: fontDisplay, fontSize: 60, fontWeight: 400, margin: 0, letterSpacing: -2 }}>Today's <em>picks.</em></h2>
      </div>
      <div style={{ display: "flex", gap: 6, marginBottom: 28, flexWrap: "wrap" }}>
        {["All", "NBA", "NFL", "MLB", "NHL", "NCAA", "Soccer"].map((t, i) => (
          <div key={t} style={{
            padding: "8px 16px", borderRadius: 999,
            background: i === 0 ? palette.text : "transparent",
            color: i === 0 ? palette.bg : palette.muted,
            border: `1px solid ${i === 0 ? palette.text : palette.border}`,
            fontSize: 12, fontWeight: 500, cursor: "pointer",
          }}>{t}</div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: selectedPick ? "repeat(2, 1fr)" : "repeat(4, 1fr)", gap: 20 }}>
        {TODAYS_GAMES.map((g, i) => (
          <AtlasGameCard key={i} g={g} palette={palette} fontDisplay={fontDisplay} fontMono={fontMono} onClick={() => setSelectedPick(g)} />
        ))}
      </div>
    </div>

    {selectedPick && (
      <div style={{ position: "sticky", top: 0, alignSelf: "start" }}>
        <AtlasGlass palette={palette} padding={32}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.gold, letterSpacing: 2 }}>SELECTION DETAIL</div>
            <button onClick={() => setSelectedPick(null)} style={{ background: "transparent", border: "none", color: palette.muted, cursor: "pointer", fontSize: 22 }}>×</button>
          </div>

          <div style={{ marginBottom: 28 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 8 }}>{selectedPick.league} · {selectedPick.time}</div>
            <div style={{ fontFamily: fontDisplay, fontSize: 30, fontWeight: 400, lineHeight: 1.15, letterSpacing: -1 }}>
              {selectedPick.away}<br/>
              <span style={{ color: palette.muted, fontStyle: "italic" }}>at</span> {selectedPick.home}
            </div>
          </div>

          <div style={{ background: palette.surface2, borderRadius: 16, padding: 24, marginBottom: 24 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 10 }}>RECOMMENDED</div>
            <div style={{ fontFamily: fontDisplay, fontSize: 38, fontWeight: 500, color: palette.accent, marginBottom: 16, letterSpacing: -1 }}>{selectedPick.pick}</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, paddingTop: 16, borderTop: `1px solid ${palette.border}` }}>
              {[["Stake", `${selectedPick.units}u`], ["Edge", selectedPick.edge], ["Confidence", `${selectedPick.confidence}%`]].map(([k, v]) => (
                <div key={k}>
                  <div style={{ fontFamily: fontMono, fontSize: 9, color: palette.muted, letterSpacing: 2, marginBottom: 4 }}>{k.toUpperCase()}</div>
                  <div style={{ fontFamily: fontDisplay, fontSize: 20, fontWeight: 500 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 16 }}>SIGNAL BREAKDOWN</div>
            {[
              { k: "Pace differential", v: 78 },
              { k: "Rest advantage", v: 64 },
              { k: "Closing line value", v: 82 },
              { k: "Lineup confidence", v: 91 },
            ].map(s => (
              <div key={s.k} style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
                  <span style={{ color: palette.muted }}>{s.k}</span>
                  <span style={{ fontFamily: fontMono, fontWeight: 500 }}>{s.v}</span>
                </div>
                <div style={{ height: 2, background: palette.surface2, position: "relative" }}>
                  <div style={{ position: "absolute", inset: 0, width: `${s.v}%`, background: palette.accent }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ fontFamily: fontDisplay, fontSize: 14, lineHeight: 1.6, color: palette.muted, fontStyle: "italic", paddingLeft: 16, borderLeft: `2px solid ${palette.gold}` }}>
            "Closing line value detected at -3.5; market drifts toward -2.5. Pace mismatch favours {selectedPick.homeAbbr} in transition."
          </div>
        </AtlasGlass>
      </div>
    )}
  </div>
);

// === HISTORY ===
const AtlasHistory = ({ palette, fontDisplay, fontSans, fontMono }) => {
  const max = Math.max(...PERFORMANCE_30D.map(d => d.units));
  const min = Math.min(0, ...PERFORMANCE_30D.map(d => d.units));
  return (
    <div style={{ padding: "56px 40px", maxWidth: 1376, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 40 }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.gold, letterSpacing: 3, textTransform: "uppercase", marginBottom: 10 }}>Model performance</div>
          <h2 style={{ fontFamily: fontDisplay, fontSize: 60, fontWeight: 400, margin: 0, letterSpacing: -2 }}>Performance.</h2>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {["7D", "30D", "90D", "YTD"].map((t, i) => (
            <div key={t} style={{
              padding: "8px 16px", borderRadius: 999,
              background: i === 1 ? palette.text : "transparent",
              color: i === 1 ? palette.bg : palette.muted,
              border: `1px solid ${i === 1 ? palette.text : palette.border}`,
              fontSize: 12, fontWeight: 500, cursor: "pointer", fontFamily: fontMono, letterSpacing: 1,
            }}>{t}</div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16, marginBottom: 28 }}>
        {[
          { k: "Win rate", v: "65.4%", d: "+1.1pp" },
          { k: "Picks", v: "187", d: "30 days" },
          { k: "Units", v: "+18.4", d: "+24%" },
          { k: "ROI", v: "+19.6%", d: "+2.3pp" },
          { k: "Avg edge", v: "3.7%", d: "+0.2pp" },
        ].map((m, i) => (
          <AtlasGlass key={i} palette={palette} padding={22}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 12 }}>{m.k}</div>
            <div style={{ fontFamily: fontDisplay, fontSize: 36, fontWeight: 400, letterSpacing: -1 }}>{m.v}</div>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.win, marginTop: 6 }}>↑ {m.d}</div>
          </AtlasGlass>
        ))}
      </div>

      <AtlasGlass palette={palette} padding={32} style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 28 }}>
          <div>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>CUMULATIVE UNITS · 30 DAYS</div>
            <div style={{ fontFamily: fontDisplay, fontSize: 36, fontWeight: 400, letterSpacing: -1 }}>+{PERFORMANCE_30D[PERFORMANCE_30D.length - 1].units.toFixed(2)}</div>
          </div>
        </div>
        <div style={{ height: 260 }}>
          <svg viewBox="0 0 800 260" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
            <defs>
              <linearGradient id="atlhfill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={palette.accent} stopOpacity="0.25"/>
                <stop offset="100%" stopColor={palette.accent} stopOpacity="0"/>
              </linearGradient>
            </defs>
            {[0, 0.25, 0.5, 0.75, 1].map(p => (
              <line key={p} x1="0" x2="800" y1={p * 260} y2={p * 260} stroke={palette.border} strokeWidth="1" />
            ))}
            <polyline points={`0,260 ${PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 250 - ((d.units - min) / (max - min)) * 240;
              return `${x},${y}`;
            }).join(" ")} 800,260`} fill="url(#atlhfill)" />
            <polyline points={PERFORMANCE_30D.map((d, i) => {
              const x = (i / 29) * 800;
              const y = 250 - ((d.units - min) / (max - min)) * 240;
              return `${x},${y}`;
            }).join(" ")} fill="none" stroke={palette.accent} strokeWidth="1.5" />
          </svg>
        </div>
      </AtlasGlass>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 28 }}>
        <AtlasGlass palette={palette} padding={28}>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 22 }}>By sport</div>
          {SPORT_BREAKDOWN.map(s => (
            <div key={s.sport} style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, alignItems: "baseline" }}>
                <span style={{ fontFamily: fontDisplay, fontSize: 16, fontWeight: 500 }}>{s.sport}</span>
                <span style={{ color: palette.muted, fontFamily: fontMono, fontSize: 11 }}>{s.picks} picks · <span style={{ color: palette.win }}>{s.winRate}%</span></span>
              </div>
              <div style={{ height: 2, background: palette.surface2, position: "relative" }}>
                <div style={{ position: "absolute", inset: 0, width: `${(s.winRate - 50) * 5}%`, background: palette.accent }} />
              </div>
            </div>
          ))}
        </AtlasGlass>

        <AtlasGlass palette={palette} padding={0}>
          <div style={{ padding: "22px 28px 14px" }}>
            <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, textTransform: "uppercase" }}>Recent picks</div>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ color: palette.muted, fontSize: 10, letterSpacing: 2, fontFamily: fontMono }}>
                <th style={{ padding: "10px 28px", textAlign: "left", fontWeight: 400 }}>DATE</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>MATCH</th>
                <th style={{ padding: "10px 0", textAlign: "left", fontWeight: 400 }}>PICK</th>
                <th style={{ padding: "10px 28px", textAlign: "right", fontWeight: 400 }}>RES</th>
                <th style={{ padding: "10px 28px 10px 0", textAlign: "right", fontWeight: 400 }}>U</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_PICKS.map((p, i) => (
                <tr key={i} style={{ borderTop: `1px solid ${palette.border}` }}>
                  <td style={{ padding: "13px 28px", color: palette.muted, fontFamily: fontMono, fontSize: 11 }}>{p.date}</td>
                  <td style={{ padding: "13px 0", fontFamily: fontDisplay, fontSize: 14 }}>{p.matchup}</td>
                  <td style={{ padding: "13px 0", fontFamily: fontMono, fontSize: 12 }}>{p.pick}</td>
                  <td style={{ padding: "13px 28px", textAlign: "right", color: p.result === "W" ? palette.win : palette.loss, fontFamily: fontMono, fontSize: 11, fontWeight: 600 }}>{p.result}</td>
                  <td style={{ padding: "13px 28px 13px 0", textAlign: "right", fontFamily: fontMono, color: p.units.startsWith("+") ? palette.win : palette.loss }}>{p.units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </AtlasGlass>
      </div>
    </div>
  );
};

// === BACKTEST ===
const AtlasBacktest = ({ palette, fontDisplay, fontSans, fontMono }) => (
  <div style={{ padding: "56px 40px", maxWidth: 1376, margin: "0 auto" }}>
    <div style={{ marginBottom: 56 }}>
      <div style={{ fontFamily: fontMono, fontSize: 11, color: palette.gold, letterSpacing: 3, textTransform: "uppercase", marginBottom: 10 }}>Provenance · 2019—2026</div>
      <h2 style={{ fontFamily: fontDisplay, fontSize: 72, fontWeight: 400, margin: "0 0 18px", letterSpacing: -2.5, lineHeight: 1.05 }}>
        Six seasons.<br/>
        <em>Every pick on record.</em>
      </h2>
      <p style={{ fontSize: 16, color: palette.muted, maxWidth: 660, lineHeight: 1.6 }}>
        Out-of-sample backtests using rolling-window training. No retroactive line shopping. No selection bias. The picks below are what the model would have published — and lost or won — in real time.
      </p>
    </div>

    <AtlasGlass palette={palette} padding={32} style={{ marginBottom: 28 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 28, alignItems: "flex-start" }}>
        <div>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, marginBottom: 6 }}>CUMULATIVE UNITS · ALL SPORTS</div>
          <div style={{ fontFamily: fontDisplay, fontSize: 48, fontWeight: 400, letterSpacing: -1.5 }}>+388.6</div>
        </div>
        <div style={{ display: "flex", gap: 18, fontSize: 11, color: palette.muted, fontFamily: fontMono, marginTop: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 12, height: 1, background: palette.accent }} /> Cumulative</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 12, borderTop: `1px dashed ${palette.muted}` }} /> Random baseline</div>
        </div>
      </div>
      <div style={{ height: 280 }}>
        <svg viewBox="0 0 800 280" style={{ width: "100%", height: "100%" }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="atlbtfill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={palette.accent} stopOpacity="0.22"/>
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
                const v = cum + s.units * tt + (Math.sin(k * 0.5 + si) * 1.5);
                const xi = (si * segPerSeason + k);
                const x = (xi / segs) * 800;
                const y = 270 - (v / total) * 250;
                pts.push(`${x},${y}`);
              }
              cum += s.units;
            });
            return (
              <>
                <polyline points={`0,280 ${pts.join(" ")} 800,280`} fill="url(#atlbtfill)" />
                <polyline points={pts.join(" ")} fill="none" stroke={palette.accent} strokeWidth="1.5" />
                <line x1="0" y1="265" x2="800" y2="265" stroke={palette.muted} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.5" />
              </>
            );
          })()}
        </svg>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12, fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
        {SEASON_BACKTEST.map(s => <span key={s.season}>{s.season}</span>)}
      </div>
    </AtlasGlass>

    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, marginBottom: 28 }}>
      {[
        { k: "Out-of-sample", v: "100%", sub: "Rolling-window training, no leakage" },
        { k: "Avg sample", v: "2,193", sub: "Picks per season" },
        { k: "Worst drawdown", v: "−12.4u", sub: "Q3 2021, 14-day window" },
      ].map((m, i) => (
        <AtlasGlass key={i} palette={palette} padding={28}>
          <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, textTransform: "uppercase", marginBottom: 14 }}>{m.k}</div>
          <div style={{ fontFamily: fontDisplay, fontSize: 48, fontWeight: 400, letterSpacing: -1.5, marginBottom: 10 }}>{m.v}</div>
          <div style={{ fontSize: 13, color: palette.muted }}>{m.sub}</div>
        </AtlasGlass>
      ))}
    </div>

    <AtlasGlass palette={palette} padding={0}>
      <div style={{ padding: "24px 32px 14px" }}>
        <div style={{ fontFamily: fontMono, fontSize: 10, color: palette.muted, letterSpacing: 2, textTransform: "uppercase" }}>Season-by-season</div>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr style={{ color: palette.muted, fontSize: 10, letterSpacing: 2, fontFamily: fontMono }}>
            <th style={{ padding: "10px 32px", textAlign: "left", fontWeight: 400 }}>SEASON</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>PICKS</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>WIN RATE</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>UNITS</th>
            <th style={{ padding: "10px 0", textAlign: "right", fontWeight: 400 }}>ROI</th>
            <th style={{ padding: "10px 32px", textAlign: "right", fontWeight: 400 }}>EQUITY</th>
          </tr>
        </thead>
        <tbody>
          {SEASON_BACKTEST.map(s => (
            <tr key={s.season} style={{ borderTop: `1px solid ${palette.border}` }}>
              <td style={{ padding: "16px 32px", fontFamily: fontDisplay, fontSize: 18, fontWeight: 500 }}>{s.season}</td>
              <td style={{ padding: "16px 0", textAlign: "right", color: palette.muted, fontFamily: fontMono }}>{s.picks.toLocaleString()}</td>
              <td style={{ padding: "16px 0", textAlign: "right", fontFamily: fontMono }}>{s.winRate}%</td>
              <td style={{ padding: "16px 0", textAlign: "right", fontFamily: fontMono, color: palette.win, fontWeight: 600 }}>+{s.units}</td>
              <td style={{ padding: "16px 0", textAlign: "right", fontFamily: fontMono }}>+{s.roi}%</td>
              <td style={{ padding: "16px 32px", textAlign: "right" }}>
                <svg width="100" height="22" viewBox="0 0 100 22" style={{ verticalAlign: "middle" }}>
                  <polyline points={Array.from({ length: 16 }, (_, k) => `${(k / 15) * 100},${20 - (s.units / 80) * (k / 15) * 20 - Math.sin(k) * 0.4}`).join(" ")}
                    fill="none" stroke={palette.accent} strokeWidth="1.2" />
                </svg>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </AtlasGlass>
  </div>
);

window.AtlasApp = AtlasApp;
