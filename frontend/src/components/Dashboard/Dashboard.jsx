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

    return (
        <div className={styles.dashboard}>
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
                            A 3-layer pipeline combining static analysis, fine‑tuned CodeBERT classification,
                            and grounded LLM tutoring to provide educational feedback for novice programmers.
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
                    <FadeUp><SectionLabel>The Problem &amp; The Idea</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Tools can show errors or even fix code, but they often do not teach the concept behind the bug.">Why This Project Exists</SectionTitle></FadeUp>

                    <FadeUp>
                        <div className={styles.cardGrid2}>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconBlue}`}>P</div>
                                <div className={styles.cardTitle}>The Problem</div>
                                <div className={styles.cardText}>
                                    Traditional tools (compilers, linters) indicate that an error exists, but they don't explain the underlying concept. Students may rely on AI to get fixes directly, missing the opportunity to learn why the bug occurred.
                                </div>
                            </GlassCard>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconGreen}`}>S</div>
                                <div className={styles.cardTitle}>The Idea</div>
                                <div className={styles.cardText}>
                                    Combine classifier‑based bug detection with a grounded tutor explanation — instead of using only one model.
                                    The classifier decides <strong>WHAT</strong> is wrong, the LLM explains <strong>WHY</strong> it is wrong.
                                </div>
                            </GlassCard>
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={styles.callout}>
                            <strong>Research Question:</strong> Can a multi-layer pipeline provide effective educational feedback for novice programmers?
                        </div>
                    </FadeUp>

                    <FadeUp>
                        <div className={styles.cardGrid3}>
                            <GlassCard className={styles.centeredCard}>
                                <div className={`${styles.cardIcon} ${styles.cardIconBlue} ${styles.cardIconCentered}`}>1</div>
                                <div className={styles.cardTitle}>Speed</div>
                                <div className={styles.cardText}>CodeBERT classifies in milliseconds on CPU; LLMs need seconds + GPU</div>
                            </GlassCard>
                            <GlassCard className={styles.centeredCard}>
                                <div className={`${styles.cardIcon} ${styles.cardIconPurple} ${styles.cardIconCentered}`}>2</div>
                                <div className={styles.cardTitle}>Reproducibility</div>
                                <div className={styles.cardText}>Classifier gives identical output every time; LLMs are stochastic</div>
                            </GlassCard>
                            <GlassCard className={styles.centeredCard}>
                                <div className={`${styles.cardIcon} ${styles.cardIconCyan} ${styles.cardIconCentered}`}>3</div>
                                <div className={styles.cardTitle}>No Hallucination</div>
                                <div className={styles.cardText}>LLMs can invent bugs that don't exist; classifiers don't hallucinate</div>
                            </GlassCard>
                        </div>
                    </FadeUp>
                </div>
            </section>

            {/* ── PIPELINE ARCHITECTURE ── */}
            <section id="architecture" className={`${styles.section} ${styles.sectionAlt}`}>
                <div className={styles.container}>
                    <FadeUp><SectionLabel>System Architecture</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Student code flows through static analysis, CodeBERT classification, and LLM-powered educational explanations.">3-Layer Pipeline</SectionTitle></FadeUp>

                    {/* Pipeline Diagram (hand-drawn) */}
                    <FadeUp>
                        <div className={styles.diagramWrapper}>
                            <img
                                src="/pipeline_diagram.png"
                                alt="3-Layer Pipeline Architecture Diagram"
                                className={styles.diagramImg}
                                onClick={() => setModalImg({ src: '/pipeline_diagram.png', alt: 'Pipeline Architecture' })}
                            />
                            <div className={styles.fcCaption}>Figure 1: End-to-end 3-layer pipeline architecture</div>
                        </div>
                    </FadeUp>

                    {/* Detailed Layer Breakdown */}
                    <FadeUp>
                        <div className={styles.detailedFlow}>
                            <div className={styles.flowSection}>
                                <div className={`${styles.flowBadge} ${styles.flowBadgeOrange}`}>Layer 1</div>
                                <div className={styles.flowContent}>
                                    <h4>Static Analysis &amp; Baselines</h4>
                                    <p>Rule-based and classical ML detection methods</p>
                                    <ul>
                                        <li><strong>Bandit</strong> — Rule-based security scanner (Python only)</li>
                                        <li><strong>Keyword Matching</strong> — String match for risky constructs (eval, exec, while True)</li>
                                        <li><strong>TF-IDF + Logistic Regression</strong> — Classical ML baseline with GridSearch tuning</li>
                                    </ul>
                                </div>
                            </div>
                            <div className={styles.connectorArrow}>|</div>
                            <div className={styles.flowSection}>
                                <div className={`${styles.flowBadge} ${styles.flowBadgePurple}`}>Layer 2</div>
                                <div className={styles.flowContent}>
                                    <h4>CodeBERT Bug Detection</h4>
                                    <p>Fine-tuned transformer classifier (125M params)</p>
                                    <ul>
                                        <li><strong>Model:</strong> microsoft/codebert-base, Focal Loss (γ=2.0)</li>
                                        <li><strong>Training:</strong> AdamW, lr=5e-6, cosine schedule, max 384 tokens</li>
                                        <li><strong>Split:</strong> 70/15/15 by unique ID — no data leakage</li>
                                        <li><strong>Threshold:</strong> Selected on validation set, frozen for test</li>
                                        <li><strong>Support:</strong> Rule-based fallback for common structural mistakes</li>
                                    </ul>
                                </div>
                            </div>
                            <div className={styles.connectorArrow}>|</div>
                            <div className={styles.flowSection}>
                                <div className={`${styles.flowBadge} ${styles.flowBadgeGreen}`}>Layer 3</div>
                                <div className={styles.flowContent}>
                                    <h4>LLM Educational Explainer</h4>
                                    <p>Qwen2.5-Coder-7B-Instruct, 4-bit quantised — not fine-tuned</p>
                                    <ul>
                                        <li><strong>Structured prompt</strong> enforces 5-section educational output</li>
                                        <li><strong>Diff injection</strong> — real unified diff injected into Section 3</li>
                                        <li><strong>Validation pipeline</strong> — format check + hallucinated diff detection</li>
                                        <li><strong>Safe fallback</strong> — template used when LLM output fails checks</li>
                                    </ul>
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
                                    { num: 1, color: '#3b82f6', title: 'Goal — What the code tries to do' },
                                    { num: 2, color: '#ef4444', title: 'The Bug — Symptom, cause, misconception' },
                                    { num: 3, color: '#10b981', title: 'The Fix — Real diff, why it works' },
                                    { num: 4, color: '#8b5cf6', title: 'Mini-Lesson — Rule of thumb, example' },
                                    { num: 5, color: '#06b6d4', title: 'Quick Check — One conceptual question' },
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
                    <FadeUp><SectionLabel>Project Work</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Main workstreams, fixes, experiments, and deployment milestones.">What I Did Across the Project</SectionTitle></FadeUp>

                    <FadeUp>
                        <div className={styles.tableWrapper}>
                            <table>
                                <thead><tr><th>Workstream</th><th>What I Did</th><th>Outcome</th></tr></thead>
                                <tbody>
                                    {[
                                        ['Datasets', 'Built Python (~930K), Java (~160K), and C# (~33K) datasets; cleaned duplicates; added synthetic bug types (16.7% of final data)', 'Multilingual training data'],
                                        ['Leakage Fix', 'Changed from random row-split to ID-based split so paired bug/fix versions stay in same split', 'Honest evaluation'],
                                        ['Model Work', 'Fine-tuned CodeBERT with Focal Loss, cosine schedule, macro-F1 threshold selection', 'Buggy / Clean classifier'],
                                        ['Inference Fixes', 'Tried long-file chunking, AST decomposition, confidence gating, code-pattern support', 'Partial improvement only'],
                                        ['LLM Work', 'Compared template, zero-shot, and structured grounded Qwen in 3-baseline experiment', 'Baseline 3 best'],
                                        ['Deployment', 'Built React + Flask + Monaco Editor + TutorPanel web application', 'Full working system'],
                                        ['Evaluation', 'Ran 1000-sample detection study, 1000-pair LLM study, 30-user survey, repeated tests', 'Final report evidence'],
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
                                The full training pipeline from data collection through ID-based splitting to model evaluation.
                            </div>
                            <div className={styles.diagramWrapper} style={{ border: 'none', padding: '0' }}>
                                <img
                                    src="/training_flowchart.png"
                                    alt="Training Pipeline Flowchart"
                                    className={styles.diagramImg}
                                    onClick={() => setModalImg({ src: '/training_flowchart.png', alt: 'Training Pipeline Flowchart' })}
                                />
                                <div className={styles.fcCaption}>Figure 2: Training pipeline and data splitting strategy</div>
                            </div>
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
                                        <tr><td className={styles.accentCell}>Python</td><td>~930K</td><td>CTSSB ~739K, Synthetic ~183K, CTSSB Aug ~7K, PyVul ~1.5K</td><td>~20% synthetic data</td></tr>
                                        <tr><td className={styles.accentCell}>Java</td><td>~160K</td><td>ManySStuBs4J, CodeXGLUE Bugs2Fix, Vul4J, HuggingFace</td><td>Multiple bug-fix sources</td></tr>
                                        <tr><td className={styles.accentCell}>C#</td><td>~33K</td><td>InferredBugs, SARD Juliet NIST, GitHub-mined, Synthetic</td><td>Smallest but highest quality</td></tr>
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
                    <FadeUp><SectionTitle sub="Fine-tuning was essential — pre-trained CodeBERT performed at or below chance level.">Pre-trained vs Fine-tuned CodeBERT</SectionTitle></FadeUp>

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
                                    <span><span className={styles.legendDot} style={{ background: '#3b82f6' }} /> Fine-tuned</span>
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
                            <strong>Key Finding:</strong> C# improved the most (+32% accuracy) with the smallest dataset (~33K). Dataset quality &gt; dataset quantity. Java reached near-Python F1 with 6× less data.
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
                        <h3 className={styles.subTitle} style={{ marginTop: '2.5rem' }}>1000-Sample Baseline Comparison</h3>
                        <p className={styles.sectionSub}>Evaluated on 1000 balanced Python samples (500 buggy, 500 clean) from the held-out test split.</p>
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
                    <FadeUp><SectionLabel>LLM Experiment &amp; User Study</SectionLabel></FadeUp>
                    <FadeUp><SectionTitle sub="Structured prompting and grounding made the explainer reliable.">Explanation Quality &amp; User Evaluation</SectionTitle></FadeUp>

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
                            <strong>Key LLM Result:</strong> The improvement came from design — structured prompting, real diff injection, validation, and safe fallback — not model size. 89.3% LLM-generated, 10.7% safe fallback.
                        </div>
                    </FadeUp>

                    {/* User Evaluation */}
                    <FadeUp>
                        <h3 className={styles.subTitle} style={{ marginTop: '3rem' }}>User Evaluation Survey</h3>
                        <div className={styles.compGrid}>
                            <GlassCard className={styles.compCard}>
                                <div className={styles.compLabel} style={{ color: '#3b82f6' }}>SUS Score</div>
                                <div className={styles.compVal}><span className={styles.gradient}>71.8</span></div>
                                <div className={styles.compSub}>"Good" band (avg = 68)</div>
                            </GlassCard>
                            <GlassCard className={styles.compCard}>
                                <div className={styles.compLabel} style={{ color: '#10b981' }}>Tutor Helpfulness</div>
                                <div className={styles.compVal} style={{ color: '#10b981' }}>4.04<span className={styles.compUnit}>/5</span></div>
                                <div className={styles.compSub}>Clarity: 3.96/5</div>
                            </GlassCard>
                            <GlassCard className={styles.compCard}>
                                <div className={styles.compLabel} style={{ color: '#8b5cf6' }}>Would Use Again</div>
                                <div className={styles.compVal} style={{ color: '#8b5cf6' }}>22<span className={styles.compUnit}>/30</span></div>
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
                                    <tr><td>Detection Accuracy Perception</td><td>19/30 accurate most of the time</td></tr>
                                    <tr><td>Valuable Learning Aid</td><td>19/30</td></tr>
                                    <tr><td>Top Requested Improvement</td><td>Explanation quality (16/30)</td></tr>
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
                                        <li>Long files remained difficult (512 token limit)</li>
                                        <li>Subtle logic bugs still challenging</li>
                                        <li>LLM requires GPU for real inference</li>
                                        <li>Overconfident false negatives (90%+ wrong)</li>
                                        <li>Single-file analysis only</li>
                                    </ul>
                                </div>
                            </GlassCard>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconGreen}`}>W</div>
                                <div className={styles.cardTitle}>What Helped</div>
                                <div className={styles.cardText}>
                                    <ul>
                                        <li>ID-based splitting fixed leakage</li>
                                        <li>Better data &gt; more data</li>
                                        <li>Focal Loss for hard examples</li>
                                        <li>Code-pattern fallback support</li>
                                        <li>Structured prompt grounding</li>
                                    </ul>
                                </div>
                            </GlassCard>
                            <GlassCard>
                                <div className={`${styles.cardIcon} ${styles.cardIconCyan}`}>F</div>
                                <div className={styles.cardTitle}>Future Work</div>
                                <div className={styles.cardText}>
                                    <ul>
                                        <li>Token-level bug localisation (GNN)</li>
                                        <li>Longer-context models (LongCoder)</li>
                                        <li>Cross-file analysis</li>
                                        <li>Fine-tuned educational explainer</li>
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
                                <div className={styles.takeaway} style={{ borderLeftColor: '#3b82f6' }}>
                                    <div className={styles.takeawayLabel} style={{ color: '#3b82f6' }}>Takeaway 1</div>
                                    <div>Built a full 3-layer educational code review system deployed as a web app.</div>
                                </div>
                                <div className={styles.takeaway} style={{ borderLeftColor: '#8b5cf6' }}>
                                    <div className={styles.takeawayLabel} style={{ color: '#8b5cf6' }}>Takeaway 2</div>
                                    <div>CodeBERT outperformed static and classical ML baselines under strict evaluation.</div>
                                </div>
                                <div className={styles.takeaway} style={{ borderLeftColor: '#10b981' }}>
                                    <div className={styles.takeawayLabel} style={{ color: '#10b981' }}>Takeaway 3</div>
                                    <div>Rigorous data handling was as important as model choice.</div>
                                </div>
                            </div>
                        </GlassCard>
                    </FadeUp>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className={styles.dashFooter}>
                <div className={styles.footerQuote}>"The classifier decides what is wrong, and the LLM explains why."</div>
                <p>AI-Powered Educational Code Analyzer · Yousef Al Dali · Computer Science FYP 2026</p>
            </footer>

            {/* Plot lightbox */}
            {modalImg && (
                <PlotModal src={modalImg.src} alt={modalImg.alt} onClose={() => setModalImg(null)} />
            )}
        </div>
    )
}
