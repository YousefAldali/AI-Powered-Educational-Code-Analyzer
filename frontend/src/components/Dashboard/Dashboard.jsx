import { useState, useEffect, useRef } from 'react'
import styles from './Dashboard.module.css'

/* ═══════════════════════════════════════════
   Data-analysis dashboard – ported from
   fyp_website/ into the React frontend.
   ═══════════════════════════════════════════ */

// ── Reusable sub-components ──────────────────

function SectionLabel({ children }) {
    return <div className={styles.sectionLabel}><span />{children}</div>
}

function SectionTitle({ children, sub }) {
    return (
        <>
            <h2 className={styles.sectionTitle}>{children}</h2>
            {sub && <p className={styles.sectionSub}>{sub}</p>}
        </>
    )
}

function GlassCard({ children, className = '', style }) {
    return <div className={`${styles.glassCard} ${className}`} style={style}>{children}</div>
}

function StatCard({ value, label }) {
    const ref = useRef(null)
    const [display, setDisplay] = useState('0')

    useEffect(() => {
        const el = ref.current
        if (!el) return
        const obs = new IntersectionObserver(([e]) => {
            if (e.isIntersecting) {
                animateValue(value, setDisplay)
                obs.unobserve(el)
            }
        }, { threshold: 0.3 })
        obs.observe(el)
        return () => obs.disconnect()
    }, [value])

    return (
        <div ref={ref} className={styles.statCard}>
            <div className={styles.statValue}>{display}</div>
            <div className={styles.statLabel}>{label}</div>
        </div>
    )
}

function animateValue(raw, setter) {
    const text = String(raw)
    const num = parseFloat(text)
    const suffix = text.replace(/[\d.]/g, '')
    if (isNaN(num)) { setter(text); return }
    const isFloat = text.includes('.')
    const start = performance.now()
    const dur = 1200
    function frame(now) {
        const t = Math.min((now - start) / dur, 1)
        const eased = 1 - Math.pow(1 - t, 3)
        const cur = num * eased
        setter((isFloat ? cur.toFixed(1) : String(Math.floor(cur))) + suffix)
        if (t < 1) requestAnimationFrame(frame)
    }
    requestAnimationFrame(frame)
}

function FadeUp({ children, className = '', style }) {
    const ref = useRef(null)
    const [visible, setVisible] = useState(false)
    useEffect(() => {
        const el = ref.current
        if (!el) return
        const obs = new IntersectionObserver(([e]) => {
            if (e.isIntersecting) { setVisible(true); obs.unobserve(el) }
        }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' })
        obs.observe(el)
        return () => obs.disconnect()
    }, [])
    return (
        <div
            ref={ref}
            className={`${styles.fadeUp} ${visible ? styles.fadeUpVisible : ''} ${className}`}
            style={style}
        >
            {children}
        </div>
    )
}

function AnimatedBar({ width, label, variant = 'blue' }) {
    const ref = useRef(null)
    const [w, setW] = useState(0)
    useEffect(() => {
        const el = ref.current
        if (!el) return
        const obs = new IntersectionObserver(([e]) => {
            if (e.isIntersecting) { setW(width); obs.unobserve(el) }
        }, { threshold: 0.2 })
        obs.observe(el)
        return () => obs.disconnect()
    }, [width])
    return (
        <div ref={ref} className={styles.barTrack}>
            <div
                className={`${styles.barFill} ${styles[`barFill_${variant}`]}`}
                style={{ width: `${w}%`, transition: 'width 1.5s cubic-bezier(0.4,0,0.2,1)' }}
            >
                {label}
            </div>
        </div>
    )
}

function Tag({ children, color = 'green' }) {
    return <span className={`${styles.tag} ${styles[`tag_${color}`]}`}>{children}</span>
}

function PlotCard({ src, alt, label, onClick }) {
    const [loaded, setLoaded] = useState(false)
    return (
        <div className={styles.plotCard} onClick={onClick}>
            {!loaded && <div className={styles.plotSkeleton}><div className={styles.shimmer} /></div>}
            <img
                src={src}
                alt={alt}
                loading="lazy"
                onLoad={() => setLoaded(true)}
                style={{ opacity: loaded ? 1 : 0, position: loaded ? 'static' : 'absolute' }}
            />
            <div className={styles.plotLabel}>{label}</div>
        </div>
    )
}

function PlotModal({ src, alt, onClose }) {
    if (!src) return null
    useEffect(() => {
        const handler = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [onClose])
    return (
        <div className={styles.plotModal} onClick={onClose}>
            <img
                src={src}
                alt={alt}
                onClick={(e) => e.stopPropagation()}
                style={{ background: '#ffffff', borderRadius: '12px', padding: '1rem' }}
            />
        </div>
    )
}

// ── Back to Top Button ──────────────────────
function BackToTop() {
    const [show, setShow] = useState(false)
    useEffect(() => {
        const onScroll = () => setShow(window.scrollY > 400)
        window.addEventListener('scroll', onScroll, { passive: true })
        return () => window.removeEventListener('scroll', onScroll)
    }, [])
    if (!show) return null
    return (
        <button
            className={styles.backToTop}
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            aria-label="Back to top"
        >
            ↑
        </button>
    )
}

// ── Section Navigation ──────────────────────
const SECTIONS = [
    { id: 'hero', label: 'Overview' },
    { id: 'problem', label: 'Problem' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'work', label: 'Project Work' },
    { id: 'results', label: 'Results' },
    { id: 'llm', label: 'LLM & Survey' },
    { id: 'conclusion', label: 'Conclusion' },
]

function SectionNav() {
    const [active, setActive] = useState('hero')
    useEffect(() => {
        const els = SECTIONS.map(s => document.getElementById(s.id)).filter(Boolean)
        const obs = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) { setActive(entry.target.id); break }
            }
        }, { rootMargin: '-20% 0px -60% 0px' })
        els.forEach(el => obs.observe(el))
        return () => obs.disconnect()
    }, [])
    return (
        <nav className={styles.sectionNav}>
            {SECTIONS.map(s => (
                <button
                    key={s.id}
                    className={`${styles.sectionNavBtn} ${active === s.id ? styles.sectionNavActive : ''}`}
                    onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                >
                    <span className={styles.sectionNavDot} />
                    <span className={styles.sectionNavLabel}>{s.label}</span>
                </button>
            ))}
        </nav>
    )
}


// ── Main Dashboard ───────────────────────────

export default function Dashboard() {
    const [modalImg, setModalImg] = useState(null)
    const [lightMode, setLightMode] = useState(false)

    return (
        <div className={`${styles.dashboard} ${lightMode ? styles.dashboardLight : ''}`}>
            <button
                className={styles.themeToggle}
                onClick={() => setLightMode(prev => !prev)}
                aria-label="Toggle theme"
                title={lightMode ? 'Switch to dark mode' : 'Switch to light mode'}
            >
                {lightMode ? '🌙' : '☀️'}
            </button>
            <SectionNav />
            <BackToTop />

            {/* ── HERO ── */}
            <section id="hero" className={styles.hero}>
                <div className={styles.heroBg} />
                <div className={styles.container}>
                    <FadeUp>
                        <div className={styles.heroBadge}>
                            <span className={styles.heroDot} />
                            Computer Science Final Year Project
                        </div>
                    </FadeUp>
                    <FadeUp>
                        <h1 className={styles.heroTitle}>
                            AI-Powered<br /><span className={styles.gradient}>Educational Code Analyzer</span>
                        </h1>
                    </FadeUp>
                    <FadeUp>
                        <p className={styles.heroDesc}>
                            A multi-layered analysis pipeline combining static analysis, transformer-based classification,
                            and LLM-generated explanations to provide effective, educational feedback for novice programmers.
                        </p>
                    </FadeUp>
                    <FadeUp>
                        <p className={styles.heroCredits}>
                            Student: <strong>Yousef Al Dali</strong> &nbsp;·&nbsp;
                            Supervisor: <strong>Dr. Abhirup Ghosh</strong> &nbsp;·&nbsp;
                            Instructor: <strong>Dr. Leandro Minku</strong>
                        </p>
                    </FadeUp>

                    <FadeUp>
                        <div className={styles.statGrid}>
                            <StatCard value="3" label="Languages (Py / Java / C#)" />
                            <StatCard value="3" label="Pipeline Layers" />
                            <StatCard value="30+" label="Survey Users" />
                            <StatCard value="71.8" label="SUS Score (Good)" />
                            <StatCard value="36+" label="Tests Run" />
                        </div>
                    </FadeUp>
                </div>
            </section>

            {/* ── PROBLEM & IDEA ── */}
            <section id="problem" className={styles.section}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>Motivation &amp; Research Question</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Existing tools fix code or flag errors — but they don't teach the concept behind the bug.">Why This Project Exists</SectionTitle></FadeUp>

                    <FadeUp>
                        <div className={styles.cardGrid2}>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconBlue}`}>P</div>
                                <div className={styles.cardTitle}>The Problem</div>
                                <div className={styles.cardText}>
                                    Compilers and linters say <em>that</em> something is wrong. Auto-fix tools silently correct it. Neither teaches <em>why</em> the bug happened.
                                </div>
                            </GlassCard>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconGreen}`}>S</div>
                                <div className={styles.cardTitle}>Our Approach</div>
                                <div className={styles.cardText}>
                                    A CodeBERT classifier decides <strong>what</strong> is wrong. A grounded LLM explains <strong>why</strong>. Fast, deterministic detection + natural-language tutoring.
                                </div>
                            </GlassCard>
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={styles.callout}>
                            <strong>Research Question:</strong> Can a multi-layered analysis pipeline combining static analysis, transformer-based classification, and LLM-generated explanations provide effective, educational feedback for novice programmers?
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={styles.cardGrid3}>
                            <GlassCard className={styles.centeredCard}>
                                <div className={`${styles.cardIcon} ${styles.cardIconBlue} ${styles.cardIconCentered}`}>1</div>
                                <div className={styles.cardTitle}>Speed &amp; Cost</div>
                                <div className={styles.cardText}>Classifier runs in milliseconds on CPU; LLM needs seconds + a GPU.</div>
                            </GlassCard>
                            <GlassCard className={styles.centeredCard}>
                                <div className={`${styles.cardIcon} ${styles.cardIconPurple} ${styles.cardIconCentered}`}>2</div>
                                <div className={styles.cardTitle}>Determinism</div>
                                <div className={styles.cardText}>Classifier gives identical output every run. LLM is stochastic — so we anchor it to ground truth.</div>
                            </GlassCard>
                            <GlassCard className={styles.centeredCard}>
                                <div className={`${styles.cardIcon} ${styles.cardIconCyan} ${styles.cardIconCentered}`}>3</div>
                                <div className={styles.cardTitle}>Grounding</div>
                                <div className={styles.cardText}>LLMs can invent bugs that don't exist. The classifier decides first, so the LLM only explains real findings.</div>
                            </GlassCard>
                        </div>
                    </FadeUp>
                </div>
            </section>

            {/* ── PIPELINE ARCHITECTURE ── */}
            <section id="architecture" className={`${styles.section} ${styles.sectionAlt}`}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>System Architecture</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Code flows through static analysis → CodeBERT classification → LLM educational explanation.">3-Layer Pipeline</SectionTitle></FadeUp>

                    {/* Pipeline Diagram (hand-drawn) */}
                    <FadeUp>
                        <GlassCard>
                        <div className={styles.flowchart}>
                            <div className={`${styles.fcNode} ${styles.fcNodeGray}`}>Student Submits Code<div className={styles.fcNodeSub}>React + Monaco Editor</div></div>
                            <div className={styles.fcArrow}>↓</div>
                            <div className={`${styles.fcNode} ${styles.fcNodeGray}`}>Language Detection<div className={styles.fcNodeSub}>.py · .java · .cs</div></div>
                            <div className={styles.fcArrow}>↓</div>
                            <div className={`${styles.fcNode} ${styles.fcNodeGreen}`}>Flask API Orchestrator</div>
                            <div className={styles.fcArrow}>↓</div>

                            <div className={styles.fcParallel}>
                                <div className={`${styles.fcLayerBox} ${styles.fcLayerOrange}`}>
                                    <div className={styles.fcLayerLabel} style={{color: 'var(--dash-orange)'}}>Layer 1</div>
                                    <div className={styles.fcLayerContent}>
                                        <div className={`${styles.fcNode} ${styles.fcNodeOrange}`}>Bandit</div>
                                        <div className={`${styles.fcNode} ${styles.fcNodeOrange}`}>Patterns</div>
                                    </div>
                                </div>
                                <div className={`${styles.fcLayerBox} ${styles.fcLayerPurple}`}>
                                    <div className={styles.fcLayerLabel} style={{color: 'var(--dash-purple)'}}>Layer 2</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodePurple}`}>CodeBERT<div className={styles.fcNodeSub}>Buggy / Clean</div></div>
                                </div>
                            </div>

                            <div className={styles.fcArrow}>↓</div>
                            <div className={`${styles.fcNode} ${styles.fcNodeBlue}`}>Verdict Combination</div>
                            <div className={styles.fcArrow}>↓</div>

                            <div className={styles.fcRow}>
                                <div className={`${styles.fcNode} ${styles.fcNodeCyan}`}>Clean ✓<div className={styles.fcNodeSub}>Done</div></div>
                                <div className={styles.fcLabel}>or buggy →</div>
                                <div className={`${styles.fcLayerBox} ${styles.fcLayerGreen}`}>
                                    <div className={styles.fcLayerLabel} style={{color: 'var(--dash-green)'}}>Layer 3</div>
                                    <div className={styles.fcRow}>
                                        <div className={`${styles.fcNode} ${styles.fcNodeGreen}`}>Qwen2.5-7B<div className={styles.fcNodeSub}>5-section prompt</div></div>
                                        <div className={styles.fcLabel}>fails →</div>
                                        <div className={`${styles.fcNode} ${styles.fcNodeRed}`}>Fallback</div>
                                    </div>
                                </div>
                            </div>

                            <div className={styles.fcArrow}>↓</div>
                            <div className={`${styles.fcNode} ${styles.fcNodeBlue}`}>JSON → React Frontend<div className={styles.fcNodeSub}>Verdict + Confidence + Explanation</div></div>
                        </div>
                        <div className={styles.fcCaption}>Figure 1 · End-to-end 3-layer pipeline architecture</div>
                        </GlassCard>
                    </FadeUp>

                    {/* Detailed Layer Breakdown */}
                    <FadeUp>
                        <div className={styles.detailedFlow}>
                            <div className={styles.flowSection}>
                                <div className={`${styles.flowBadge} ${styles.flowBadgeOrange}`}>Layer 1</div>
                                <div className={styles.flowContent}>
                                    <h4>Static Analysis &amp; Rule-Based Detection</h4>
                                    <ul>
                                        <li><strong>Bandit</strong> — security scanner (Python only)</li>
                                        <li><strong>Pattern detectors</strong> — regex + AST rules for Python, Java, C# (swapped operators, off-by-one, mutable defaults, resource leaks, etc.)</li>
                                    </ul>
                                </div>
                            </div>
                            <div className={styles.connectorArrow}>|</div>
                            <div className={styles.flowSection}>
                                <div className={`${styles.flowBadge} ${styles.flowBadgePurple}`}>Layer 2</div>
                                <div className={styles.flowContent}>
                                    <h4>CodeBERT Semantic Classification</h4>
                                    <p>Fine-tuned microsoft/codebert-base (125M params)</p>
                                    <ul>
                                        <li><strong>Focal Loss</strong> (γ=2.0) · AdamW · cosine schedule · 384-token limit</li>
                                        <li><strong>ID-based split</strong> (70/15/15) — no data leakage</li>
                                        <li><strong>Threshold</strong> selected on validation, frozen for test</li>
                                        <li><strong>Long files:</strong> AST chunking (Python) / regex extraction (Java, C#) + 3-tier confidence gating</li>
                                    </ul>
                                </div>
                            </div>
                            <div className={styles.connectorArrow}>|</div>
                            <div className={styles.flowSection}>
                                <div className={`${styles.flowBadge} ${styles.flowBadgeGreen}`}>Layer 3</div>
                                <div className={styles.flowContent}>
                                    <h4>LLM Educational Explainer</h4>
                                    <p>Qwen2.5-Coder-7B-Instruct · 4-bit NF4 · not fine-tuned</p>
                                    <ul>
                                        <li><strong>5-section prompt</strong> — Goal, Bug, Fix, Mini-Lesson, Quick Check</li>
                                        <li><strong>Format validation</strong> — enforces structure before returning</li>
                                        <li><strong>Deterministic fallback</strong> — template used when GPU unavailable or output fails checks</li>
                                    </ul>
                                    <p style={{fontSize: '0.8rem', opacity: 0.7, marginTop: '0.5rem'}}>Offline evaluation used real diff injection + hallucinated-diff detection over 1000 pairs.</p>
                                </div>
                            </div>
                        </div>
                    </FadeUp>

                    {/* 5-Section Output Format */}
                    <FadeUp>
                        <GlassCard style={{ marginTop: '2rem' }}>
                            <div className={styles.cardTitle} style={{ marginBottom: '1rem' }}>Structured 5-Section Output Format</div>
                            <div className={styles.outputSections}>
                                {[
                                    { num: 1, color: '#4a7cc9', title: 'Goal — What the code tries to do' },
                                    { num: 2, color: '#c96161', title: 'The Bug — Symptom, cause, misconception' },
                                    { num: 3, color: '#5ba88a', title: 'The Fix — Real diff, why it works' },
                                    { num: 4, color: '#7b6cb5', title: 'Mini-Lesson — Rule of thumb, example' },
                                    { num: 5, color: '#5b9ebd', title: 'Quick Check — One conceptual question' },
                                ].map((s) => (
                                    <div key={s.num} className={styles.outputSection} style={{ borderLeftColor: s.color }}>
                                        <div className={styles.outputSectionLabel} style={{ color: s.color }}>Section {s.num}</div>
                                        <div className={styles.outputSectionTitle}>{s.title}</div>
                                    </div>
                                ))}
                            </div>
                        </GlassCard>
                    </FadeUp>
                </div>
            </section>

            {/* ── WORKSTREAMS TABLE ── */}
            <section id="work" className={styles.section}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>Implementation</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle>Project Workstreams</SectionTitle></FadeUp>

                    <FadeUp>
                        <div className={styles.tableWrapper}>
                            <table>
                                <thead><tr><th>Workstream</th><th>What I Did</th><th>Outcome</th></tr></thead>
                                <tbody>
                                    {[
                                        ['Data', 'Python ~930K, Java ~160K, C# ~33K pairs; cleaned, deduplicated, synthetic bugs added', 'Multilingual corpora'],
                                        ['Leakage Fix', 'Random split → ID-based 70/15/15 split (paired bug/fix stays together)', 'Honest evaluation'],
                                        ['Training', 'Focal Loss, AdamW, cosine schedule, early stopping (patience 4), threshold on validation', 'Classifiers for 3 languages'],
                                        ['Inference', 'AST chunking (Python), regex extraction (Java/C#), 3-tier confidence gating, pattern override', 'Robust real-time pipeline'],
                                        ['LLM', '5-section prompt + validation + fallback; 3-baseline comparison', 'Structured grounded (B3) best'],
                                        ['Web App', 'React + Flask + Monaco Editor + TutorPanel', 'Deployed system'],
                                        ['Evaluation', '1000-sample detection, 1000-pair LLM study, 30-user survey (SUS)', 'Full evidence base'],
                                    ].map(([ws, did, outcome], i) => (
                                        <tr key={i}>
                                            <td className={styles.accentCell}>{ws}</td>
                                            <td>{did}</td>
                                            <td>{outcome}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </FadeUp>

                    {/* Training Flowchart (hand-drawn) */}
                    <FadeUp>
                        <GlassCard style={{ marginTop: '2.5rem' }}>
                            <div className={styles.cardTitle}>Training Pipeline &amp; Data Flow</div>
                            <div className={styles.cardText} style={{ marginBottom: '1rem' }}>
                                Data is deduplicated, normalised, and ID-split so paired buggy/fixed versions never leak across train/val/test.
                            </div>
                            <div className={styles.flowchart}>
                                <div className={`${styles.fcNode} ${styles.fcNodeGreen}`}>Python (~930K), Java (~160K), C# (~33K)<div className={styles.fcNodeSub}>Raw datasets</div></div>
                                <div className={styles.fcArrow}>↓</div>

                                <div className={styles.fcRow}>
                                    <div className={`${styles.fcNode} ${styles.fcNodeGray}`} style={{maxWidth: '160px'}}>Remove Identical<div className={styles.fcNodeSub}>buggy == fixed</div></div>
                                    <div className={styles.fcRowArrow}>→</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeGray}`} style={{maxWidth: '160px'}}>Length Filter<div className={styles.fcNodeSub}>Remove trivial / oversized</div></div>
                                    <div className={styles.fcRowArrow}>→</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeGray}`} style={{maxWidth: '160px'}}>MD5 Dedup<div className={styles.fcNodeSub}>Within &amp; across sources</div></div>
                                    <div className={styles.fcRowArrow}>→</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeGray}`} style={{maxWidth: '160px'}}>Source Pruning<div className={styles.fcNodeSub}>Remove noisy sources</div></div>
                                </div>

                                <div className={styles.fcArrow}>↓</div>

                                <div className={styles.fcRow} style={{gap: '2rem'}}>
                                    <div className={`${styles.fcNode} ${styles.fcNodeOrange}`}>ID-Based Train / Val / Test Split<div className={styles.fcNodeSub}>70 / 15 / 15</div></div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeRed}`} style={{maxWidth: '220px'}}>⚠ Data Leakage Risk<div className={styles.fcNodeSub}>Random split = buggy in train, fixed in test</div></div>
                                </div>

                                <div className={styles.fcArrow}>↓</div>
                                <div className={`${styles.fcNode} ${styles.fcNodeGray}`}>BPE Tokenisation<div className={styles.fcNodeSub}>RoBERTa tokenizer · 384 tokens</div></div>
                                <div className={styles.fcArrow}>↓</div>

                                <div className={styles.fcRow}>
                                    <div className={`${styles.fcNode} ${styles.fcNodePurple}`}>CodeBERT Fine-Tuning<div className={styles.fcNodeSub}>Focal Loss · AdamW · Cosine</div></div>
                                    <div className={styles.fcRowArrow}>→</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeBlue}`}>3 Trained Models<div className={styles.fcNodeSub}>Python · Java · C#</div></div>
                                </div>

                                <div className={styles.fcArrow}>↓</div>

                                <div className={styles.fcRow}>
                                    <div className={`${styles.fcNode} ${styles.fcNodeCyan}`}>Threshold on Validation<div className={styles.fcNodeSub}>Optimise Macro-F1</div></div>
                                    <div className={styles.fcRowArrow}>→</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeCyan}`}>Test Evaluation<div className={styles.fcNodeSub}>Threshold frozen</div></div>
                                    <div className={styles.fcRowArrow}>→</div>
                                    <div className={`${styles.fcNode} ${styles.fcNodeGreen}`}>Deployed in Pipeline<div className={styles.fcNodeSub}>Frozen model + threshold</div></div>
                                </div>
                            </div>
                            <div className={styles.fcCaption}>Figure 2: Training pipeline and data splitting strategy</div>
                        </GlassCard>
                    </FadeUp>

                    {/* Dataset Composition */}
                    <FadeUp>
                        <GlassCard style={{ marginTop: '1.5rem' }}>
                            <div className={styles.cardTitle} style={{ marginBottom: '1rem' }}>Dataset Composition</div>
                            <div className={styles.tableWrapper}>
                                <table>
                                    <thead><tr><th>Language</th><th>Total Size</th><th>Sources</th><th>Notes</th></tr></thead>
                                    <tbody>
                                        <tr><td className={styles.accentCell}>Python</td><td>~930K</td><td>CTSSB, Synthetic (20+ bug types), PyVul</td><td>16.7% synthetic</td></tr>
                                        <tr><td className={styles.accentCell}>Java</td><td>~160K</td><td>ManySStuBs4J, CodeXGLUE, Vul4J</td><td>Real-world bug-fix repos</td></tr>
                                        <tr><td className={styles.accentCell}>C#</td><td>~33K</td><td>InferredBugs, SARD Juliet, GitHub-mined</td><td>Smallest but highest quality</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </GlassCard>
                    </FadeUp>
                </div>
            </section>

            {/* ── RESULTS ── */}
            <section id="results" className={`${styles.section} ${styles.sectionAlt}`}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>Experiments &amp; Results</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Pre-trained CodeBERT scored at chance level (~50%) — fine-tuning was essential.">Pre-trained vs Fine-tuned CodeBERT</SectionTitle></FadeUp>

                    <FadeUp>
                        <div className={styles.cardGrid2}>
                            {/* Accuracy Bar Chart */}
                            <GlassCard>
                                <div className={styles.cardTitle} style={{ marginBottom: '1rem' }}>Accuracy Comparison</div>
                                <div className={styles.barChart}>
                                    {[
                                        { lang: 'Python', pre: 51.5, fine: 66.3 },
                                        { lang: 'Java', pre: 48, fine: 65.8 },
                                        { lang: 'C#', pre: 50, fine: 82, green: true },
                                    ].map((d) => (
                                        <div key={d.lang} className={styles.barGroup}>
                                            <div className={styles.barLabel}>{d.lang}</div>
                                            <AnimatedBar width={d.pre} label={`${d.pre}%`} variant="gray" />
                                            <AnimatedBar width={d.fine} label={`${d.fine}%`} variant={d.green ? 'green' : 'blue'} />
                                        </div>
                                    ))}
                                </div>
                                <div className={styles.chartLegend}>
                                    <span><span className={styles.legendDot} style={{ background: 'rgba(100,116,139,0.4)' }} /> Pre-trained</span>
                                    <span><span className={styles.legendDot} style={{ background: '#4a7cc9' }} /> Fine-tuned</span>
                                </div>
                            </GlassCard>

                            {/* Full Results Table */}
                            <GlassCard>
                                <div className={styles.cardTitle} style={{ marginBottom: '1rem' }}>Full Results Table</div>
                                <div className={styles.tableWrapper}>
                                    <table>
                                        <thead><tr><th>Lang</th><th>Metric</th><th>Pre</th><th>Fine</th><th>Gain</th></tr></thead>
                                        <tbody>
                                            {[
                                                ['Python','Accuracy','51.5%','66.3%','+14.8'],
                                                ['Python','Macro-F1','0.51','0.66','+0.15'],
                                                ['Python','AUC','0.51','0.76','+0.25'],
                                                ['Java','Accuracy','48.0%','65.8%','+17.8'],
                                                ['Java','Macro-F1','0.48','0.66','+0.18'],
                                                ['Java','AUC','0.47','0.74','+0.27'],
                                                ['C#','Accuracy','50.0%','82.0%','+32.0'],
                                                ['C#','Macro-F1','0.33','0.82','+0.49'],
                                                ['C#','AUC','0.33','0.93','+0.60'],
                                            ].map(([l,m,p,f,g], i) => (
                                                <tr key={i}><td>{l}</td><td>{m}</td><td>{p}</td><td>{f}</td><td className={styles.highlightCell}>{g}</td></tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </GlassCard>
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={`${styles.callout} ${styles.calloutGreen}`}>
                            <strong>Key Finding:</strong> C# gained +32% accuracy with the smallest dataset (~33K). Data quality &gt; quantity. Java matched Python's F1 with 6× less data.
                        </div>
                    </FadeUp>

                    {/* Final Detection Results */}
                    <FadeUp>
                        <h3 className={styles.subTitle}>Final Detection Results</h3>
                        <div className={styles.tableWrapper}>
                            <table>
                                <thead><tr><th>Language</th><th>Dataset Size</th><th>Macro-F1</th><th>AUC</th><th>AP</th><th>Accuracy</th><th>Clean Recall</th><th>Buggy Recall</th></tr></thead>
                                <tbody>
                                    <tr><td className={styles.accentCell}>Python</td><td>~930K</td><td>0.66</td><td>0.76</td><td>0.77</td><td className={styles.highlightCell}>66.3%</td><td>68.1%</td><td>64.6%</td></tr>
                                    <tr><td className={styles.accentCell}>Java</td><td>~160K</td><td>0.66</td><td>0.74</td><td>0.71</td><td className={styles.highlightCell}>65.8%</td><td>61.0%</td><td>70.5%</td></tr>
                                    <tr><td className={styles.accentCell}>C#</td><td>~33K</td><td>0.82</td><td>0.93</td><td>0.93</td><td className={styles.highlightCell}>82.0%</td><td>83.2%</td><td>80.8%</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </FadeUp>

                    {/* Baseline Comparison */}
                    <FadeUp>
                        <h3 className={styles.subTitle} style={{ marginTop: '2.5rem' }}>1000-Sample Detection Study</h3>
                        <p className={styles.sectionSub}>1000 balanced Python samples (500 buggy + 500 clean) from the held-out test split.</p>
                        <div className={styles.tableWrapper}>
                            <table>
                                <thead><tr><th>Method</th><th>Accuracy</th><th>Macro-F1</th><th>Buggy Recall</th><th>Clean Recall</th></tr></thead>
                                <tbody>
                                    <tr><td>Bandit (Static Analysis)</td><td>50.0%</td><td>0.35</td><td>2.0%</td><td>98.0%</td></tr>
                                    <tr><td>Keyword Matching</td><td>50.0%</td><td>0.37</td><td>4.4%</td><td>95.6%</td></tr>
                                    <tr><td>TF-IDF + Logistic Regression</td><td>49.6%</td><td>0.48</td><td>32.4%</td><td>66.8%</td></tr>
                                    <tr className={styles.highlightRow}>
                                        <td className={styles.accentCell}><strong>CodeBERT (Fine-tuned)</strong></td>
                                        <td className={styles.highlightCell}><strong>66.3%</strong></td>
                                        <td className={styles.highlightCell}><strong>0.66</strong></td>
                                        <td className={styles.highlightCell}><strong>64.6%</strong></td>
                                        <td className={styles.highlightCell}><strong>68.1%</strong></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </FadeUp>

                    {/* Report Figures — Key Comparisons */}
                    <FadeUp>
                        <h3 className={styles.subTitle} style={{ marginTop: '3rem' }}>Key Experiment Figures</h3>
                        <p className={styles.sectionSub}>Publication-quality figures from the report, summarising training and evaluation.</p>
                        <div className={styles.plotsGrid}>
                            {[
                                { src: '/fig_pretrained_vs_finetuned.png', alt: 'Pre-trained vs Fine-tuned', label: 'Pre-trained vs Fine-tuned CodeBERT' },
                                { src: '/fig_cross_language.png', alt: 'Cross-Language Performance', label: 'Cross-Language Final Performance' },
                                { src: '/fig_detection_baselines.png', alt: 'Detection Baselines', label: 'Detection Methods Comparison (1000 Samples)' },
                                { src: '/fig_training_curves.png', alt: 'Training Curves', label: 'Validation Performance Across Epochs' },
                                { src: '/fig_training_loss.png', alt: 'Training Loss', label: 'Training Loss Convergence (All Languages)' },
                                { src: '/fig_codebert_vs_graphcodebert.png', alt: 'CodeBERT vs GraphCodeBERT', label: 'CodeBERT vs GraphCodeBERT Comparison' },
                            ].map((p) => (
                                <PlotCard
                                    key={p.src}
                                    src={p.src}
                                    alt={p.alt}
                                    label={p.label}
                                    onClick={() => setModalImg(p)}
                                />
                            ))}
                        </div>
                    </FadeUp>

                    {/* Python Model Evaluation Plots */}
                    <FadeUp>
                        <h3 className={styles.subTitle} style={{ marginTop: '3rem' }}>Python Model Evaluation Plots</h3>
                        <p className={styles.sectionSub}>Detailed CodeBERT Python evaluation (threshold = 0.494, selected on validation set).</p>
                        <div className={styles.plotsGrid}>
                            {[
                                { src: '/confusion_matrix.png', alt: 'Confusion Matrix', label: 'Confusion Matrix' },
                                { src: '/roc_curve.png', alt: 'ROC Curve', label: 'ROC Curve (AUC = 0.756)' },
                                { src: '/precision_recall_curve_python.png', alt: 'Precision-Recall Curve', label: 'Precision-Recall Curve (AP = 0.770)' },
                                { src: '/threshold_sweep_macro_f1.png', alt: 'Threshold Sweep Macro-F1', label: 'Threshold Sweep: Macro-F1' },
                                { src: '/threshold_sweep_recalls.png', alt: 'Threshold Sweep Recalls', label: 'Threshold Sweep: Clean vs Buggy Recall' },
                                { src: '/length_dist_python_test.png', alt: 'Token Length Distribution (Test)', label: 'Token Length Distribution (Test Set)' },
                                { src: '/length_dist_python_val.png', alt: 'Token Length Distribution (Val)', label: 'Token Length Distribution (Validation Set)' },
                                { src: '/length_overlay_python_test.png', alt: 'Length Overlay (Test)', label: 'Length Overlay: Buggy vs Clean (Test)' },
                                { src: '/length_overlay_python_val.png', alt: 'Length Overlay (Val)', label: 'Length Overlay: Buggy vs Clean (Validation)' },
                            ].map((p) => (
                                <PlotCard
                                    key={p.src}
                                    src={p.src}
                                    alt={p.alt}
                                    label={p.label}
                                    onClick={() => setModalImg(p)}
                                />
                            ))}
                        </div>
                    </FadeUp>
                </div>
            </section>

            {/* ── LLM EXPERIMENT & USER STUDY ── */}
            <section id="llm" className={styles.section}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>LLM Evaluation &amp; User Study</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="3-baseline comparison over 1000 buggy–fixed pairs + 30-participant user survey.">Explanation Quality &amp; User Evaluation</SectionTitle></FadeUp>

                    {/* LLM Baselines & Survey Report Figures */}
                    <FadeUp>
                        <h3 className={styles.subTitle}>LLM Experiment &amp; Survey Figures</h3>
                        <div className={styles.plotsGrid}>
                            {[
                                { src: '/fig_llm_baselines.png', alt: 'LLM Baselines Comparison', label: 'LLM Explanation Quality: 3-Baseline Comparison' },
                                { src: '/fig_survey_results.png', alt: 'User Survey Results', label: 'User Evaluation Survey (n=30)' },
                            ].map((p) => (
                                <PlotCard
                                    key={p.src}
                                    src={p.src}
                                    alt={p.alt}
                                    label={p.label}
                                    onClick={() => setModalImg(p)}
                                />
                            ))}
                        </div>
                    </FadeUp>

                    {/* LLM Results Table */}
                    <FadeUp>
                        <div className={styles.tableWrapper}>
                            <table>
                                <thead><tr><th>Metric</th><th>B1 — Template</th><th>B2 — Zero-Shot</th><th>B3 — Structured</th></tr></thead>
                                <tbody>
                                    <tr><td>5-Section Format</td><td><Tag color="green">100%</Tag></td><td><Tag color="red">0%</Tag></td><td><Tag color="green">100%</Tag></td></tr>
                                    <tr><td>Hallucinated Diff Lines</td><td><Tag color="green">0%</Tag></td><td><Tag color="red">27.8%</Tag></td><td><Tag color="green">0%</Tag></td></tr>
                                    <tr><td>Bug-Specific Explanation</td><td><Tag color="red">No</Tag></td><td><Tag color="green">Yes</Tag></td><td><Tag color="green">Yes</Tag></td></tr>
                                    <tr><td>Grounded in Real Diff</td><td><Tag color="green">Yes</Tag></td><td><Tag color="red">No</Tag></td><td><Tag color="green">Yes</Tag></td></tr>
                                </tbody>
                            </table>
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={`${styles.callout} ${styles.calloutPurple}`}>
                            <strong>Key LLM Finding:</strong> Improvement came from prompt design, not model size. 89.3% LLM-generated, 10.7% safe fallback.
                        </div>
                    </FadeUp>

                    {/* User Evaluation */}
                    <FadeUp>
                        <h3 className={styles.subTitle} style={{ marginTop: '3rem' }}>User Evaluation (n=30)</h3>
                        <div className={styles.compGrid}>
                            <GlassCard className={styles.compCard}>
                                <div className={styles.compLabel} style={{ color: '#4a7cc9' }}>SUS Score</div>
                                <div className={styles.compVal}><span className={styles.gradient}>71.8</span></div>
                                <div className={styles.compSub}>"Good" band (avg = 68)</div>
                            </GlassCard>
                            <GlassCard className={styles.compCard}>
                                <div className={styles.compLabel} style={{ color: '#5ba88a' }}>Tutor Helpfulness</div>
                                <div className={styles.compVal} style={{ color: '#5ba88a' }}>4.04<span className={styles.compUnit}>/5</span></div>
                                <div className={styles.compSub}>Clarity: 3.96/5</div>
                            </GlassCard>
                            <GlassCard className={styles.compCard}>
                                <div className={styles.compLabel} style={{ color: '#7b6cb5' }}>Would Use Again</div>
                                <div className={styles.compVal} style={{ color: '#7b6cb5' }}>22<span className={styles.compUnit}>/30</span></div>
                                <div className={styles.compSub}>Overall rating: 3.92/5</div>
                            </GlassCard>
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={styles.tableWrapper} style={{ marginTop: '1.5rem' }}>
                            <table>
                                <thead><tr><th>Metric</th><th>Result</th></tr></thead>
                                <tbody>
                                    <tr><td>Participants</td><td>30 (undergrad, postgrad, professionals)</td></tr>
                                    <tr><td>Accurate Most of the Time</td><td>19/30</td></tr>
                                    <tr><td>Valuable Learning Aid</td><td>19/30</td></tr>
                                    <tr><td>Would Use Again</td><td>22/30</td></tr>
                                    <tr><td>Top Improvement Request</td><td>Explanation quality (16/30)</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </FadeUp>
                </div>
            </section>

            {/* ── LIMITATIONS & CONCLUSION ── */}
            <section id="conclusion" className={`${styles.section} ${styles.sectionAlt}`}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>Limitations, Future Work &amp; Conclusion</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle>Honest Strengths &amp; Weaknesses</SectionTitle></FadeUp>

                    <FadeUp>
                        <div className={styles.cardGrid3}>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconOrange}`}>L</div>
                                <div className={styles.cardTitle}>Main Limitations</div>
                                <div className={styles.cardText}>
                                    <ul>
                                        <li>384-token limit — long files lose cross-function context</li>
                                        <li>Single-file only — no cross-file reasoning</li>
                                        <li>LLM needs GPU; falls back to templates without one</li>
                                        <li>Overconfident false negatives (90%+ wrong sometimes)</li>
                                        <li>30-participant convenience sample only</li>
                                    </ul>
                                </div>
                            </GlassCard>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconGreen}`}>W</div>
                                <div className={styles.cardTitle}>What Helped</div>
                                <div className={styles.cardText}>
                                    <ul>
                                        <li>ID-based splitting fixed data leakage</li>
                                        <li>Quality &gt; quantity (C# best with smallest data)</li>
                                        <li>Focal Loss for hard examples</li>
                                        <li>Pattern detectors override false negatives</li>
                                        <li>Structured prompting = no hallucinations</li>
                                    </ul>
                                </div>
                            </GlassCard>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconCyan}`}>F</div>
                                <div className={styles.cardTitle}>Future Work</div>
                                <div className={styles.cardText}>
                                    <ul>
                                        <li>More languages (Haskell, Rust, Go)</li>
                                        <li>Longer-context models (LongCoder)</li>
                                        <li>Cross-file reasoning</li>
                                        <li>Controlled classroom study with pre/post tests</li>
                                    </ul>
                                </div>
                            </GlassCard>
                        </div>
                    </FadeUp>

                    {/* Final Takeaways */}
                    <FadeUp>
                        <GlassCard style={{ marginTop: '2.5rem', textAlign: 'center', padding: '3rem 2rem' }}>
                            <div className={styles.cardTitle} style={{ fontSize: '1.3rem', marginBottom: '1.5rem' }}>Final Takeaways</div>
                            <div className={styles.takeawayGrid}>
                                <div className={styles.takeaway} style={{ borderLeftColor: '#4a7cc9' }}>
                                    <div className={styles.takeawayLabel} style={{ color: '#4a7cc9' }}>Takeaway 1</div>
                                    <div>Built and deployed a full 3-layer educational code review system as a web app.</div>
                                </div>
                                <div className={styles.takeaway} style={{ borderLeftColor: '#7b6cb5' }}>
                                    <div className={styles.takeawayLabel} style={{ color: '#7b6cb5' }}>Takeaway 2</div>
                                    <div>CodeBERT outperformed all baselines on all three languages under strict evaluation.</div>
                                </div>
                                <div className={styles.takeaway} style={{ borderLeftColor: '#5ba88a' }}>
                                    <div className={styles.takeawayLabel} style={{ color: '#5ba88a' }}>Takeaway 3</div>
                                    <div>Rigorous data handling was as important as model choice.</div>
                                </div>
                            </div>
                        </GlassCard>
                    </FadeUp>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className={styles.dashFooter}>
                <div className={styles.footerQuote}>"The classifier decides what is wrong; the LLM explains why."</div>
                <p>AI-Powered Educational Code Analyzer · Yousef Al Dali · Computer Science FYP 2026</p>
            </footer>

            {/* Plot lightbox */}
            {modalImg && (
                <PlotModal src={modalImg.src} alt={modalImg.alt} onClose={() => setModalImg(null)} />
            )}
        </div>
    )
}
