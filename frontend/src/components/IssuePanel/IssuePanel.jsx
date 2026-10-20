import { useState, useRef, useEffect, useCallback } from 'react'
import {
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  ExternalLink,
  Wand2,
  Maximize2,
} from 'lucide-react'
import styles from './IssuePanel.module.css'

// ── Severity shape icons (custom SVGs, not emoji) ──

export function SeverityIcon({ severity, size = 12 }) {
  const colors = {
    error: 'var(--severity-error)',
    warning: 'var(--severity-warning)',
    info: 'var(--severity-info)',
    style: 'var(--severity-style)',
  }
  const color = colors[severity] || colors.info

  if (severity === 'error') {
    // Filled triangle
    return (
      <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden="true" style={{ flexShrink: 0 }}>
        <polygon points="6,1 11,10.5 1,10.5" fill={color} />
      </svg>
    )
  }
  if (severity === 'warning') {
    // Filled diamond
    return (
      <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden="true" style={{ flexShrink: 0 }}>
        <polygon points="6,1 11,6 6,11 1,6" fill={color} />
      </svg>
    )
  }
  if (severity === 'info') {
    // Filled circle
    return (
      <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden="true" style={{ flexShrink: 0 }}>
        <circle cx="6" cy="6" r="4.5" fill={color} />
      </svg>
    )
  }
  // style: dash
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden="true" style={{ flexShrink: 0 }}>
      <line x1="2" y1="6" x2="10" y2="6" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export const SEVERITY_LABELS = { error: 'Error', warning: 'Warning', info: 'Info', style: 'Style' }
export const TYPE_LABELS = { bug: 'Bug', security: 'Security', performance: 'Performance', style: 'Style' }

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* ignore */ }
  }

  return (
    <button
      className={styles.actionBtn}
      onClick={handleCopy}
      title="Copy fix to clipboard"
      aria-label="Copy fix"
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

// ── Diff preview (unified) ──

function DiffPreview({ fix }) {
  if (!fix) return null
  const beforeLines = fix.before.split('\n')
  const afterLines = fix.after.split('\n')

  return (
    <div className={styles.diff}>
      <div className={styles.diffHeader}>Fix preview</div>
      <pre className={styles.diffCode}>
        {beforeLines.map((line, i) => (
          <div key={`r-${i}`} className={styles.diffRemove}>
            <span className={styles.diffSign}>−</span>
            {line}
          </div>
        ))}
        {afterLines.map((line, i) => (
          <div key={`a-${i}`} className={styles.diffAdd}>
            <span className={styles.diffSign}>+</span>
            {line}
          </div>
        ))}
      </pre>
    </div>
  )
}

// ── Single issue row ──

function IssueItem({
  issue,
  isExpanded,
  isFocused,
  onToggle,
  onLineClick,
  onApplyFix,
  onInspect,
  isFixed,
}) {
  const ref = useRef(null)

  useEffect(() => {
    if (isFocused && ref.current) {
      ref.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [isFocused])

  const severityClass = styles[`severity_${issue.severity}`] || ''

  return (
    <div
      ref={ref}
      className={`${styles.issue} ${isExpanded ? styles.issueExpanded : ''} ${isFocused ? styles.issueFocused : ''} ${isFixed ? styles.issueFixed : ''}`}
      role="option"
      aria-selected={isFocused}
      id={`issue-${issue.id}`}
      tabIndex={-1}
    >
      {/* Collapsed header */}
      <div
        className={styles.issueHeader}
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={`issue-detail-${issue.id}`}
        role="button"
        tabIndex={0}
      >
        <span className={styles.issueChevron}>
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
        <SeverityIcon severity={issue.severity} />
        <span className={`${styles.severityBadge} ${severityClass}`}>
          {SEVERITY_LABELS[issue.severity]}
        </span>
        <span className={styles.typeBadge}>{TYPE_LABELS[issue.type]}</span>
        <span className={styles.issueTitle}>
          {issue.title}
          {isFixed && <span className={styles.fixedBadge}>Fixed</span>}
        </span>
        <button
          className={styles.lineLink}
          onClick={(e) => {
            e.stopPropagation()
            onLineClick?.(issue.line)
          }}
          title={`Go to line ${issue.line}`}
        >
          L{issue.line}
        </button>
      </div>

      {/* Expanded detail */}
      {isExpanded && (
        <div className={styles.issueDetail} id={`issue-detail-${issue.id}`}>
          <div className={styles.explanation}>{issue.explanation}</div>

          <DiffPreview fix={issue.fix} />

          <div className={styles.issueActions}>
            {issue.fix && onApplyFix && (
              <button
                className={`${styles.actionBtn} ${styles.applyBtn} ${isFixed ? styles.appliedBtn : ''}`}
                onClick={() => onApplyFix(issue)}
                disabled={isFixed}
                title={isFixed ? 'Fix already applied' : 'Apply fix to editor'}
              >
                <Wand2 size={13} />
                {isFixed ? 'Applied' : 'Apply fix'}
              </button>
            )}

            <CopyButton text={issue.fix?.after || ''} />

            {onInspect && (
              <button
                className={styles.actionBtn}
                onClick={() => onInspect(issue)}
                title="Open deep-dive tutor explanation"
              >
                <Maximize2 size={13} />
                Deep dive
              </button>
            )}

            {issue.toolUrl && (
              <a
                href={issue.toolUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.toolLink}
              >
                <ExternalLink size={12} />
                {issue.tool} {issue.toolRule}
              </a>
            )}
          </div>

          {issue.example && (
            <div className={styles.exampleSection}>
              <div className={styles.exampleLabel}>Correct example</div>
              <pre className={styles.exampleCode}>{issue.example}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main issue panel ──

export default function IssuePanel({
  issues = [],
  onLineClick,
  onApplyFix,
  onInspect,
  fixedIssueIds = new Set(),
  activeLine = null,
  filterType = null,
  filterSeverity = null,
}) {
  const [expandedIds, setExpandedIds] = useState(new Set())
  const [focusIndex, setFocusIndex] = useState(-1)
  const panelRef = useRef(null)

  // Auto-expand issue when active line changes
  useEffect(() => {
    if (activeLine) {
      const matching = issues.find((iss) => iss.line === activeLine)
      if (matching) {
        setExpandedIds((prev) => new Set([...prev, matching.id]))
      }
    }
  }, [activeLine, issues])

  function toggleIssue(id) {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Filter issues if filters applied
  const filteredIssues = issues.filter((iss) => {
    if (filterType && iss.type !== filterType) return false
    if (filterSeverity && iss.severity !== filterSeverity) return false
    return true
  })

  // Keyboard navigation (j/k/Enter)
  const handleKeyDown = useCallback(
    (e) => {
      if (!filteredIssues.length) return

      if (e.key === 'j' || e.key === 'ArrowDown') {
        e.preventDefault()
        setFocusIndex((prev) => Math.min(prev + 1, filteredIssues.length - 1))
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        e.preventDefault()
        setFocusIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter' && focusIndex >= 0) {
        e.preventDefault()
        toggleIssue(filteredIssues[focusIndex].id)
      }
    },
    [filteredIssues, focusIndex]
  )

  // Group issues by type
  const grouped = filteredIssues.reduce((acc, issue) => {
    const type = issue.type || 'other'
    if (!acc[type]) acc[type] = []
    acc[type].push(issue)
    return acc
  }, {})

  // Ordered type groups
  const typeOrder = ['bug', 'security', 'performance', 'style']
  const sortedGroups = typeOrder
    .filter((t) => grouped[t]?.length)
    .map((t) => ({ type: t, issues: grouped[t] }))

  // Flatten for j/k index mapping
  let flatIndex = 0

  return (
    <div
      ref={panelRef}
      className={styles.panel}
      role="listbox"
      aria-label="Review issues"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {sortedGroups.length === 0 && (
        <div className={styles.noIssues}>
          <Check size={20} className={styles.noIssuesIcon} />
          <div className={styles.noIssuesTitle}>No issues found</div>
          <div className={styles.noIssuesSub}>
            The code looks clean. Static analysis and pattern checks passed without flagging anything.
          </div>
        </div>
      )}

      {sortedGroups.map(({ type, issues: groupIssues }) => (
        <div key={type} className={styles.group}>
          <div className={styles.groupHeader}>
            <span className={styles.groupLabel}>{TYPE_LABELS[type]}</span>
            <span className={styles.groupCount}>{groupIssues.length}</span>
          </div>
          {groupIssues.map((issue) => {
            const myIndex = flatIndex++
            return (
              <IssueItem
                key={issue.id}
                issue={issue}
                index={myIndex}
                isExpanded={expandedIds.has(issue.id)}
                isFocused={focusIndex === myIndex}
                onToggle={() => toggleIssue(issue.id)}
                onLineClick={onLineClick}
                onApplyFix={onApplyFix}
                onInspect={onInspect}
                isFixed={fixedIssueIds.has(issue.id)}
              />
            )
          })}
        </div>
      ))}
    </div>
  )
}
