import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './TutorPanel.module.css'

// Helper components for the different feedback sub-sections

function Verdict({ label, codebertLabel, hasStaticIssues }) {
    const isBuggy = label?.toLowerCase() === 'buggy'
    const isUncertain = label?.toLowerCase() === 'uncertain'

    // Determine the subtitle based on what actually flagged the code
    let subtitle = 'No deep logical bugs were detected. Great work!'
    if (isBuggy) {
        const cbClean = codebertLabel?.toLowerCase() === 'clean'
        if (cbClean && hasStaticIssues) {
            subtitle = 'Security issues were found by static analysis (Bandit).'
        } else if (hasStaticIssues) {
            subtitle = 'Issues found by both CodeBERT and static analysis.'
        } else {
            subtitle = 'CodeBERT found potential logical issues in your code.'
        }
    } else if (isUncertain) {
        subtitle = 'CodeBERT is uncertain — review the details below.'
    }

    // Pick the right visual style for each state
    const verdictStyle = isBuggy
        ? styles.verdictBuggy
        : isUncertain
            ? styles.verdictUncertain
            : styles.verdictClean

    const verdictIcon = isBuggy ? '⚠' : isUncertain ? '?' : '✓'
    const verdictTitle = isBuggy ? 'Issues Detected' : isUncertain ? 'Needs Review' : 'Clean Code!'

    return (
        <div className={`${styles.verdict} ${verdictStyle}`}>
            <span className={styles.verdictIcon}>{verdictIcon}</span>
            <div>
                <div className={styles.verdictTitle}>{verdictTitle}</div>
                <div className={styles.verdictSub}>{subtitle}</div>
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

// Loading animation while waiting for API

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

// Placeholder when no code is submitted yet

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

// Error message display

function ErrorState({ message }) {
    return (
        <div className={styles.errorState}>
            <span className={styles.errorIcon}>✕</span>
            <div className={styles.errorTitle}>Something went wrong</div>
            <div className={styles.errorMsg}>{message}</div>
        </div>
    )
}

// The main panel

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
                        <Verdict
                            label={result.prediction?.label}
                            codebertLabel={result.prediction?.codebert_label}
                            hasStaticIssues={result.static_analysis?.issues?.length > 0}
                        />
                        <StaticIssues issues={result.static_analysis?.issues} />
                        <TutorExplanation explanation={result.educational_explanation} />
                    </div>
                )}
            </div>
        </div>
    )
}
