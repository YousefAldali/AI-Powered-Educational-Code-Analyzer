import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './TutorPanel.module.css'

// ─── Sub-components ──────────────────────────────────────────────────────────

function Verdict({ label }) {
    const isBuggy = label?.toLowerCase() === 'buggy'
    return (
        <div className={`${styles.verdict} ${isBuggy ? styles.verdictBuggy : styles.verdictClean}`}>
            <span className={styles.verdictIcon}>{isBuggy ? '⚠' : '✓'}</span>
            <div>
                <div className={styles.verdictTitle}>{isBuggy ? 'Bugs Detected' : 'Clean Code!'}</div>
                <div className={styles.verdictSub}>
                    {isBuggy
                        ? 'CodeBERT found potential logical issues in your code.'
                        : 'No deep logical bugs were detected. Great work!'}
                </div>
            </div>
        </div>
    )
}

function StaticIssues({ issues }) {
    if (!issues || issues.length === 0) return null
    return (
        <div className={styles.section}>
            <div className={styles.sectionHeader}>
                <span className={styles.sectionIcon}>◈</span>
                <span className={styles.sectionTitle}>Static Analysis</span>
                <span className={styles.badge}>{issues.length}</span>
            </div>
            <ul className={styles.issueList}>
                {issues.map((issue, i) => (
                    <li key={i} className={styles.issueItem}>
                        <span className={styles.issueBullet}>›</span>
                        <code className={styles.issueText}>{issue}</code>
                    </li>
                ))}
            </ul>
        </div>
    )
}

function TutorExplanation({ explanation }) {
    if (!explanation) return null
    return (
        <div className={styles.section}>
            <div className={styles.sectionHeader}>
                <span className={styles.sectionIcon}>✦</span>
                <span className={styles.sectionTitle}>AI Tutor Explanation</span>
                <span className={styles.poweredBy}>Qwen2.5-Coder</span>
            </div>
            <div className={`tutor-markdown ${styles.markdownBody}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {explanation}
                </ReactMarkdown>
            </div>
        </div>
    )
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────

function LoadingState() {
    return (
        <div className={styles.loadingWrapper}>
            <div className={styles.spinner} />
            <div className={styles.loadingTitle}>AI Tutor is analyzing your code…</div>
            <div className={styles.loadingSteps}>
                <LoadingStep delay={0} label="Running static analysis" />
                <LoadingStep delay={600} label="Running CodeBERT inference" />
                <LoadingStep delay={1400} label="Generating educational explanation" />
            </div>
        </div>
    )
}

function LoadingStep({ label, delay }) {
    return (
        <div className={styles.loadingStep} style={{ animationDelay: `${delay}ms` }}>
            <span className={styles.loadingDot} />
            {label}
        </div>
    )
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyState() {
    return (
        <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>⟡</div>
            <div className={styles.emptyTitle}>Awaiting your code</div>
            <div className={styles.emptySub}>
                Paste or type code in the editor, then click <strong>Submit for Review</strong>.
                The AI Tutor will explain any issues it finds.
            </div>
        </div>
    )
}

// ─── Error state ──────────────────────────────────────────────────────────────

function ErrorState({ message }) {
    return (
        <div className={styles.errorState}>
            <span className={styles.errorIcon}>✕</span>
            <div className={styles.errorTitle}>Something went wrong</div>
            <div className={styles.errorMsg}>{message}</div>
        </div>
    )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function TutorPanel({ result, isLoading, error }) {
    return (
        <div className={styles.panel}>
            <div className={styles.panelHeader}>
                <span className={styles.panelTitle}>Tutor Feedback</span>
            </div>

            <div className={styles.panelBody}>
                {isLoading && <LoadingState />}
                {!isLoading && error && <ErrorState message={error} />}
                {!isLoading && !error && !result && <EmptyState />}

                {!isLoading && !error && result && (
                    <div className={styles.results}>
                        <Verdict label={result.prediction?.label} />
                        <StaticIssues issues={result.static_analysis?.issues} />
                        <TutorExplanation explanation={result.educational_explanation} />
                    </div>
                )}
            </div>
        </div>
    )
}
