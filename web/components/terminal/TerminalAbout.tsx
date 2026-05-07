'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO, FONT_SANS } from '@/lib/palette'

interface Props {
  palette: Palette
}

export function TerminalAbout({ palette }: Props) {
  return (
    <div style={{ padding: '48px 32px 80px' }}>
      <div style={{ maxWidth: 980, margin: '0 auto' }}>
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 2,
            marginBottom: 16,
          }}
        >
          ◆ ABOUT / TECHNICAL DETAIL
        </div>
        <h1
          style={{
            fontSize: 56,
            lineHeight: 1.0,
            fontWeight: 500,
            letterSpacing: -1.5,
            margin: '0 0 28px',
            fontFamily: FONT_SANS,
          }}
        >
          Smart sports picks,
          <br />
          <span style={{ color: palette.muted }}>without the smoke.</span>
        </h1>
        <p
          style={{
            fontSize: 16,
            lineHeight: 1.55,
            color: palette.muted,
            maxWidth: 700,
            margin: '0 0 40px',
          }}
        >
          Axiom is a sports-betting model. It reads the odds at every major sportsbook, decides
          where the price is wrong, and publishes the games it likes. Every pick is logged so
          you can see how it actually performed — wins, losses, and dry stretches.
        </p>
        <p
          style={{
            fontSize: 14,
            lineHeight: 1.55,
            color: palette.muted,
            maxWidth: 700,
            margin: '0 0 56px',
            fontStyle: 'italic',
          }}
        >
          Looking for a non-technical walkthrough? See <strong>02 / HOW IT WORKS</strong> on
          the Home tab. The breakdown below is for readers who want the model and pipeline
          spelled out.
        </p>

        <div
          style={{
            background: palette.surface,
            border: `1px solid ${palette.border}`,
            borderLeft: `2px solid ${palette.blue}`,
            padding: 36,
            marginBottom: 32,
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.blue,
              letterSpacing: 1.5,
              marginBottom: 20,
            }}
          >
            TECHNICAL DETAIL
          </div>

          <Section palette={palette} title="The pipeline">
            <pre style={preStyle(palette)}>
{`SportsBookReview.com
  → scraper       (per-sport URL builders, HTML → DataFrame)
  → SQLite cache  (games + cached_keys; 5-season seed)
  → packager      (odds → implied probability, scores → labels)
  → models        (Naive Bayes + logistic regression ensemble)
  → bet sizer     (fractional Kelly, capped to bankroll fraction)
  → daily picks   → REST API → this site`}
            </pre>
          </Section>

          <Section palette={palette} title="The model">
            We treat each sportsbook&apos;s moneyline on a game as an independent signal and
            condition a posterior over <code>{'P(win | lines)'}</code>. The Naive Bayes model is
            paired with a logistic-regression prior on the same features so the ensemble
            doesn&apos;t collapse when book counts are thin. Prior is applied once per game, not
            once per book.
          </Section>

          <Section palette={palette} title="Walk-forward training">
            For every backtested date <code>D</code>, the training set is every cached game in
            the same season strictly before <code>D</code>. There&apos;s no leakage from future
            games. The cache holds the last five seasons per sport so the early-season window
            still has a meaningful prior. Cache misses raise — backtests refuse to silently
            run on incomplete data.
          </Section>

          <Section palette={palette} title="Bet sizing &amp; edge">
            Edge per game is <code>EV = p × (decimal_odds − 1) − (1 − p)</code> where{' '}
            <code>p</code> is the model&apos;s win probability and the line is the best price
            we can find across books. A pick is published when <code>EV ≥ 0</code> on the
            best line, with bet size set by fractional Kelly. EV{' '}{'<'} 0 ⇒ NO BET. Because
            the model is comparing to <em>real</em> book prices (not opener), edges in the
            5–8% range are typical for in-season slates.
          </Section>

          <Section palette={palette} title="Backtesting &amp; metrics">
            Every season&apos;s aggregate is persisted in <code>backtest_history</code>: win
            rate, units (flat + Kelly), ROI, and max drawdown. Max drawdown here is the
            <em> furthest the cumulative-units curve dips below the starting bankroll of
            zero</em> — i.e. the worst red number you&apos;d have seen on the unit ledger
            during the season. The History tab shows a rolling-window backtest (7d / 30d /
            90d) recomputed daily by a background thread.
          </Section>

          <Section palette={palette} title="Coverage">
            Nine leagues, moneyline-only: NBA, NHL, MLB, MLS, WNBA, NCAAB, NFL, NCAAF, CFL.
            Spreads and totals are not modeled.
          </Section>
        </div>

        {/* Model descriptions */}
        <div
          style={{
            background: palette.surface,
            border: `1px solid ${palette.border}`,
            borderLeft: `2px solid ${palette.accent}`,
            padding: 36,
            marginBottom: 32,
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.accent,
              letterSpacing: 1.5,
              marginBottom: 20,
            }}
          >
            MODEL REFERENCE
          </div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 500,
              letterSpacing: -0.3,
              marginBottom: 24,
            }}
          >
            Two models, different tradeoffs. Pick the one that fits how you bet.
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 20,
              marginBottom: 8,
            }}
          >
            {/* V1 card */}
            <div
              style={{
                background: palette.surface2,
                border: `1px solid ${palette.border2}`,
                borderTop: `2px solid ${palette.blue}`,
                padding: 24,
              }}
            >
              <div
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 10,
                  color: palette.blue,
                  letterSpacing: 1.5,
                  marginBottom: 10,
                }}
              >
                V1 · LOGREG
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
                Base model — fires on every positive-EV game
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.65, color: palette.text, marginBottom: 16 }}>
                <strong>How it works:</strong> For each game, a Naive Bayes classifier and a
                logistic regression are each trained on the current season&apos;s historical
                odds. Their outputs are combined into a win probability. A pick fires whenever
                the expected value is positive — i.e. the model&apos;s probability, multiplied
                by the decimal odds, exceeds 1.0.
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.65, color: palette.text }}>
                <strong>When to use V1:</strong> More picks per day, especially at the start
                of a season when the meta-gate hasn&apos;t seen enough history to be
                selective. Good for users who want higher volume and are comfortable with
                more variance.
              </div>
              <div
                style={{
                  marginTop: 16,
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                  color: palette.muted,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <span>● PICK RULE: EV ≥ 0</span>
                <span>● SIZING: fractional Kelly on EV</span>
                <span>● VOLUME: higher — fires on most slates</span>
              </div>
            </div>

            {/* V2 card */}
            <div
              style={{
                background: palette.surface2,
                border: `1px solid ${palette.border2}`,
                borderTop: `2px solid ${palette.accent}`,
                padding: 24,
              }}
            >
              <div
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 10,
                  color: palette.accent,
                  letterSpacing: 1.5,
                  marginBottom: 10,
                }}
              >
                V2 · LOGREG + META-GATE ★ DEFAULT
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
                Filtered model — only fires when the gate approves
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.65, color: palette.text, marginBottom: 16 }}>
                <strong>How it works:</strong> V1&apos;s base model runs first. Its output
                (EV, confidence, line magnitude, book agreement, sport) is then scored by a{' '}
                <em>meta-gate</em> — a gradient-boosted regressor trained offline on
                walk-forward backtests to predict realized kelly units. The pick only fires
                when the gate&apos;s predicted units exceed a per-sport threshold. Both the
                gate and thresholds are retrained weekly without any future-data leakage.
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.65, color: palette.text }}>
                <strong>When to use V2:</strong> Fewer, higher-conviction picks. The gate
                filters out marginal positive-EV games where V1&apos;s base model tends to
                be noisy. Better risk-adjusted performance in backtests; expect dry spells
                of several days, especially mid-season.
              </div>
              <div
                style={{
                  marginTop: 16,
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                  color: palette.muted,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <span>● PICK RULE: gate predicted_units &gt; threshold</span>
                <span>● SIZING: Kelly via gate score</span>
                <span>● VOLUME: lower — selective by design</span>
              </div>
            </div>
          </div>

          <div
            style={{
              marginTop: 20,
              padding: '14px 18px',
              background: palette.surface,
              border: `1px solid ${palette.border}`,
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              lineHeight: 1.6,
            }}
          >
            <span style={{ color: palette.text }}>TIP:</span> The rolling and season backtests
            on the Backtest tab let you compare both models side-by-side on completed data
            before committing to one. V2 is the default because it has better risk-adjusted
            numbers in out-of-sample backtests, but V1 gives you a fallback on days V2 finds
            nothing.
          </div>
        </div>

        {/* Legal disclaimer */}
        <div
          style={{
            background: palette.surface,
            border: `1px solid ${palette.border}`,
            borderLeft: `2px solid ${palette.danger ?? palette.muted}`,
            padding: 28,
            marginTop: 8,
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.danger ?? palette.muted,
              letterSpacing: 1.5,
              marginBottom: 16,
            }}
          >
            ◆ LEGAL DISCLAIMER
          </div>
          <div
            style={{
              fontSize: 13,
              lineHeight: 1.7,
              color: palette.muted,
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            <p style={{ margin: 0 }}>
              <strong style={{ color: palette.text }}>For informational and entertainment purposes only.</strong>{' '}
              Nothing on this site constitutes financial, investment, or sports-betting advice. Axiom is a
              research project that models historical odds data. It does not recommend that you place any bet.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: palette.text }}>21+ and jurisdiction compliance required.</strong>{' '}
              You must be at least 21 years of age (or the legal gambling age in your jurisdiction, whichever
              is higher) to use this site. Sports betting is not legal in all jurisdictions. It is your sole
              responsibility to know and comply with the laws of your location before placing any wager.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: palette.text }}>Past performance does not guarantee future results.</strong>{' '}
              All backtest results, win rates, and unit figures displayed on this site reflect historical
              model performance on completed games. Sports outcomes are inherently unpredictable and no model
              can guarantee profitable results going forward.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: palette.text }}>Gambling involves risk.</strong>{' '}
              Never bet more than you can afford to lose. If you or someone you know has a gambling problem,
              help is available at{' '}
              <span style={{ color: palette.text, textDecoration: 'underline' }}>1-800-GAMBLER</span>{' '}
              (1-800-426-2537) or{' '}
              <span style={{ color: palette.text, textDecoration: 'underline' }}>ncpgambling.org</span>.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: palette.text }}>No affiliation.</strong>{' '}
              Axiom has no affiliation with any sportsbook, sports league, or gambling operator. Odds data
              is sourced from publicly available information. This site does not accept bets.
            </p>
          </div>
        </div>

        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 10,
            color: palette.muted,
            letterSpacing: 1,
            textAlign: 'center',
            paddingTop: 24,
            opacity: 0.6,
          }}
        >
          © {new Date().getFullYear()} AXIOM PICKS · FOR INFORMATIONAL PURPOSES ONLY · NOT FINANCIAL ADVICE · 21+
        </div>
      </div>
    </div>
  )
}

function Section({
  palette,
  title,
  children,
}: {
  palette: Palette
  title: string
  children: React.ReactNode
}) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: palette.muted,
          letterSpacing: 1.5,
          marginBottom: 8,
        }}
      >
        ◆ {title.toUpperCase()}
      </div>
      <div style={{ fontSize: 14, lineHeight: 1.65, color: palette.text }}>{children}</div>
    </div>
  )
}

function preStyle(palette: Palette): React.CSSProperties {
  return {
    fontFamily: FONT_MONO,
    fontSize: 12,
    color: palette.text,
    background: palette.surface2,
    padding: 16,
    margin: '8px 0 0',
    borderLeft: `2px solid ${palette.border2}`,
    overflowX: 'auto',
    lineHeight: 1.6,
  }
}
