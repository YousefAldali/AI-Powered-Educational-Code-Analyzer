import { useState } from 'react'
import {
  FileCode,
  Clock,
  Sparkles,
  RotateCcw,
  Download,
  ChevronDown,
  ChevronUp,
  CheckCheck,
} from 'lucide-react'
import { SeverityIcon } from '../IssuePanel/IssuePanel'
import styles from './SummaryBar.module.css'

export default function SummaryBar({
  filename = 'student_lookup.py',
  language = 'python',
  reviewTime = 14,
  summary = '',
  issues = [],
  fixedCount = 0,
  activeFilter = null,
  onFilterChange,
  onApplyAllFixes,
  onResetCode,
  onExportJson,
}) {
  const [summaryExpanded, setSummaryExpanded] = useState(true)

  // Calculate severity counts
  const counts = {
    error: issues.filter((i) => i.severity === 'error').length,
    warning: issues.filter((i) => i.severity === 'warning').length,
    info: issues.filter((i) => i.severity === 'info').length,
    style: issues.filter((i) => i.severity === 'style').length,
  }

  const totalIssues = issues.length
  const remainingIssues = Math.max(0, totalIssues - fixedCount)

  return (
    <div className={styles.bar}>
      {/* ── Main Toolbar Strip ── */}
      <div className={styles.toolbar}>
        <div className={styles.leftGroup}>
          <div className={styles.fileIdentity}>
            <FileCode size={15} className={styles.fileIcon} />
            <span className={styles.fileName}>{filename}</span>
            <span className={styles.langBadge}>{language.toUpperCase()}</span>
          </div>

          <div className={styles.divider} />

          <div className={styles.timeBadge} title="Static analysis and AI review duration">
            <Clock size={13} />
            <span>Reviewed in {reviewTime} s</span>
          </div>

          <div className={styles.divider} />

          {/* Severity filter chips */}
          <div className={styles.severityChips} role="group" aria-label="Filter by severity">
            <button
              className={`${styles.chip} ${!activeFilter ? styles.chipActive : ''}`}
              onClick={() => onFilterChange?.(null)}
              title="Show all issues"
            >
              <span>All</span>
              <span className={styles.chipCount}>{remainingIssues}</span>
            </button>

            {counts.error > 0 && (
              <button
                className={`${styles.chip} ${activeFilter === 'error' ? styles.chipActive : ''}`}
                onClick={() => onFilterChange?.(activeFilter === 'error' ? null : 'error')}
                title="Filter errors"
              >
                <SeverityIcon severity="error" size={11} />
                <span>Errors</span>
                <span className={`${styles.chipCount} ${styles.chipError}`}>{counts.error}</span>
              </button>
            )}

            {counts.warning > 0 && (
              <button
                className={`${styles.chip} ${activeFilter === 'warning' ? styles.chipActive : ''}`}
                onClick={() => onFilterChange?.(activeFilter === 'warning' ? null : 'warning')}
                title="Filter warnings"
              >
                <SeverityIcon severity="warning" size={11} />
                <span>Warnings</span>
                <span className={`${styles.chipCount} ${styles.chipWarning}`}>{counts.warning}</span>
              </button>
            )}

            {counts.info > 0 && (
              <button
                className={`${styles.chip} ${activeFilter === 'info' ? styles.chipActive : ''}`}
                onClick={() => onFilterChange?.(activeFilter === 'info' ? null : 'info')}
                title="Filter info"
              >
                <SeverityIcon severity="info" size={11} />
                <span>Info</span>
                <span className={`${styles.chipCount} ${styles.chipInfo}`}>{counts.info}</span>
              </button>
            )}
          </div>
        </div>

        <div className={styles.rightGroup}>
          {fixedCount > 0 && (
            <button
              className={styles.toolBtn}
              onClick={onResetCode}
              title="Reset code to original submission"
            >
              <RotateCcw size={13} />
              <span>Reset</span>
            </button>
          )}

          {remainingIssues > 0 && onApplyAllFixes && (
            <button
              className={`${styles.toolBtn} ${styles.primaryToolBtn}`}
              onClick={onApplyAllFixes}
              title="Apply all suggested fixes to code"
            >
              <CheckCheck size={13} />
              <span>Apply all fixes</span>
            </button>
          )}

          {onExportJson && (
            <button
              className={styles.toolBtn}
              onClick={onExportJson}
              title="Export review report as JSON"
            >
              <Download size={13} />
              <span>Export</span>
            </button>
          )}

          {summary && (
            <button
              className={`${styles.toolBtn} ${summaryExpanded ? styles.activeSummaryToggle : ''}`}
              onClick={() => setSummaryExpanded(!summaryExpanded)}
              title={summaryExpanded ? 'Hide code summary' : 'Show code summary'}
            >
              <Sparkles size={13} />
              <span>Summary</span>
              {summaryExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
          )}
        </div>
      </div>

      {/* ── Expandable "What this code does" Summary Strip ── */}
      {summary && summaryExpanded && (
        <div className={styles.summaryDrawer}>
          <div className={styles.summaryLabel}>
            <span className={styles.summaryDot} />
            WHAT THIS CODE DOES
          </div>
          <p className={styles.summaryText}>{summary}</p>
        </div>
      )}
    </div>
  )
}
