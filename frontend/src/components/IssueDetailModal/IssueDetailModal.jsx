import { useEffect } from 'react'
import {
  X,
  ExternalLink,
  Wand2,
  Copy,
  Check,
  BookOpen,
  ShieldAlert,
  Code2,
} from 'lucide-react'
import { SeverityIcon, SEVERITY_LABELS, TYPE_LABELS } from '../IssuePanel/IssuePanel'
import { useState } from 'react'
import styles from './IssueDetailModal.module.css'

export default function IssueDetailModal({
  issue,
  onClose,
  onApplyFix,
  isFixed = false,
}) {
  const [copied, setCopied] = useState(false)

  // Escape key to close
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!issue) return null

  async function handleCopy() {
    if (!issue.fix?.after) return
    try {
      await navigator.clipboard.writeText(issue.fix.after)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* ignore */ }
  }

  const beforeLines = issue.fix?.before?.split('\n') || []
  const afterLines = issue.fix?.after?.split('\n') || []

  return (
    <div className={styles.overlay} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <div className={styles.metaBadges}>
              <SeverityIcon severity={issue.severity} size={14} />
              <span className={`${styles.severityBadge} ${styles[`severity_${issue.severity}`]}`}>
                {SEVERITY_LABELS[issue.severity]}
              </span>
              <span className={styles.typeBadge}>{TYPE_LABELS[issue.type]}</span>
              <span className={styles.lineBadge}>Line {issue.line}</span>
              {isFixed && <span className={styles.fixedBadge}>Fixed in editor</span>}
            </div>

            <button className={styles.closeBtn} onClick={onClose} aria-label="Close dialog">
              <X size={16} />
            </button>
          </div>

          <h2 className={styles.title}>{issue.title}</h2>
        </div>

        {/* Modal Body */}
        <div className={styles.body}>
          {/* Explanation Section */}
          <div className={styles.section}>
            <div className={styles.sectionHeading}>
              <BookOpen size={14} className={styles.sectionIcon} />
              <span>Tutor Explanation</span>
            </div>
            <div className={styles.explanationText}>
              {issue.explanation.split('\n\n').map((paragraph, idx) => (
                <p key={idx}>{paragraph}</p>
              ))}
            </div>
          </div>

          {/* Diff Before / After */}
          {issue.fix && (
            <div className={styles.section}>
              <div className={styles.sectionHeading}>
                <Code2 size={14} className={styles.sectionIcon} />
                <span>Proposed Change</span>
              </div>
              <div className={styles.diffContainer}>
                <div className={styles.diffHeader}>Unified Patch</div>
                <pre className={styles.diffCode}>
                  {beforeLines.map((line, i) => (
                    <div key={`r-${i}`} className={styles.diffRemove}>
                      <span className={styles.diffSign}>−</span>
                      <span>{line}</span>
                    </div>
                  ))}
                  {afterLines.map((line, i) => (
                    <div key={`a-${i}`} className={styles.diffAdd}>
                      <span className={styles.diffSign}>+</span>
                      <span>{line}</span>
                    </div>
                  ))}
                </pre>
              </div>
            </div>
          )}

          {/* Correct Example */}
          {issue.example && (
            <div className={styles.section}>
              <div className={styles.sectionHeading}>
                <ShieldAlert size={14} className={styles.sectionIcon} />
                <span>Canonical Correct Pattern</span>
              </div>
              <pre className={styles.exampleBox}>{issue.example}</pre>
            </div>
          )}

          {/* Tool Attribution */}
          {issue.tool && (
            <div className={styles.section}>
              <div className={styles.toolCard}>
                <div className={styles.toolMeta}>
                  <span className={styles.toolLabel}>Discovered by</span>
                  <span className={styles.toolName}>{issue.tool}</span>
                  {issue.toolRule && <span className={styles.ruleBadge}>{issue.toolRule}</span>}
                </div>
                {issue.toolUrl && (
                  <a
                    href={issue.toolUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.toolDocLink}
                  >
                    <span>View official documentation</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div className={styles.footer}>
          <button className={styles.secondaryBtn} onClick={onClose}>
            Done
          </button>

          <div className={styles.footerRight}>
            {issue.fix?.after && (
              <button className={styles.secondaryBtn} onClick={handleCopy}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
                <span>{copied ? 'Copied' : 'Copy fix'}</span>
              </button>
            )}

            {issue.fix && onApplyFix && (
              <button
                className={styles.primaryBtn}
                onClick={() => {
                  onApplyFix(issue)
                  onClose()
                }}
                disabled={isFixed}
              >
                <Wand2 size={14} />
                <span>{isFixed ? 'Applied' : 'Apply fix to code'}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
