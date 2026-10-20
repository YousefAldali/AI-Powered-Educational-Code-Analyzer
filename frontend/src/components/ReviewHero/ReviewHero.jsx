import { useState, useRef, useCallback } from 'react'
import CodeEditor from '../CodeEditor/CodeEditor'
import IssuePanel from '../IssuePanel/IssuePanel'
import SummaryBar from '../SummaryBar/SummaryBar'
import IssueDetailModal from '../IssueDetailModal/IssueDetailModal'
import { Check } from 'lucide-react'
import styles from './ReviewHero.module.css'

export default function ReviewHero({
  initialCode,
  reviewData,
  onResetToSubmit,
}) {
  const [code, setCode] = useState(initialCode || reviewData?.code || '')
  const [fixedIssueIds, setFixedIssueIds] = useState(new Set())
  const [activeLine, setActiveLine] = useState(null)
  const [inspectedIssue, setInspectedIssue] = useState(null)
  const [activeFilter, setActiveFilter] = useState(null)
  const [toastMessage, setToastMessage] = useState(null)
  const editorWrapperRef = useRef(null)

  const issues = reviewData?.issues || []

  // Active issues that are not fixed yet (or show all with isFixed property)
  const activeIssues = issues.filter((iss) => !fixedIssueIds.has(iss.id))

  // Show a quick transient toast
  const showToast = useCallback((msg) => {
    setToastMessage(msg)
    setTimeout(() => {
      setToastMessage((curr) => (curr === msg ? null : curr))
    }, 2800)
  }, [])

  // Handle clicking line in IssuePanel to jump editor
  function handleLineClick(line) {
    setActiveLine(line)
    if (editorWrapperRef.current) {
      CodeEditor.revealLine(editorWrapperRef.current, line)
    }
  }

  // Handle applying a single fix to the code
  function handleApplyFix(issue) {
    if (!issue.fix || fixedIssueIds.has(issue.id)) return

    const { before, after } = issue.fix
    if (!code.includes(before)) {
      // Try fuzzy whitespace matching if direct replacement fails
      const trimmedBefore = before.trim()
      const lines = code.split('\n')
      const lineIdx = lines.findIndex((l) => l.trim() === trimmedBefore)
      if (lineIdx !== -1) {
        lines[lineIdx] = after
        setCode(lines.join('\n'))
        setFixedIssueIds((prev) => new Set([...prev, issue.id]))
        showToast(`Applied fix for: ${issue.title}`)
        return
      }
      showToast('Could not automatically patch line (code modified)')
      return
    }

    setCode((prev) => prev.replace(before, after))
    setFixedIssueIds((prev) => new Set([...prev, issue.id]))
    showToast(`Applied fix for: ${issue.title}`)
  }

  // Apply all fixes in order
  function handleApplyAllFixes() {
    let newCode = code
    const applied = []

    for (const issue of issues) {
      if (issue.fix && !fixedIssueIds.has(issue.id)) {
        if (newCode.includes(issue.fix.before)) {
          newCode = newCode.replace(issue.fix.before, issue.fix.after)
          applied.push(issue.id)
        }
      }
    }

    if (applied.length > 0) {
      setCode(newCode)
      setFixedIssueIds((prev) => new Set([...prev, ...applied]))
      showToast(`Applied ${applied.length} fixes to code`)
    }
  }

  // Reset code to original
  function handleResetCode() {
    setCode(initialCode || reviewData?.code || '')
    setFixedIssueIds(new Set())
    showToast('Reset code to original submission')
  }

  // Export review report as JSON
  function handleExportJson() {
    const data = {
      filename: reviewData?.filename,
      language: reviewData?.language,
      reviewedAt: new Date().toISOString(),
      reviewDurationSeconds: reviewData?.reviewTime,
      summary: reviewData?.summary,
      totalIssues: issues.length,
      fixedIssues: fixedIssueIds.size,
      issues: issues.map((i) => ({
        ...i,
        fixed: fixedIssueIds.has(i.id),
      })),
      code,
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${reviewData?.filename || 'code_review'}_report.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('Exported review report to JSON')
  }

  return (
    <div className={styles.container}>
      {/* ── Summary Bar on Top ── */}
      <SummaryBar
        filename={reviewData?.filename || 'code.py'}
        language={reviewData?.language || 'python'}
        reviewTime={reviewData?.reviewTime || 14}
        summary={reviewData?.summary}
        issues={issues}
        fixedCount={fixedIssueIds.size}
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        onApplyAllFixes={handleApplyAllFixes}
        onResetCode={handleResetCode}
        onExportJson={handleExportJson}
      />

      {/* ── Split IDE View: Left 55% Code, Right 45% Feedback ── */}
      <div className={styles.split}>
        {/* Left: Code Viewer */}
        <section className={styles.codePane} ref={editorWrapperRef}>
          <div className={styles.paneHeader}>
            <div className={styles.paneTitle}>
              <span className={styles.paneDot} />
              <span>SOURCE VIEWER</span>
            </div>
            <span className={styles.paneHint}>
              Click line numbers or issue badges to jump
            </span>
          </div>

          <div className={styles.editorContainer}>
            <CodeEditor
              value={code}
              onChange={setCode}
              language={reviewData?.language || 'python'}
              issues={activeIssues}
              onLineClick={handleLineClick}
            />
          </div>
        </section>

        {/* Vertical Divider */}
        <div className={styles.divider} />

        {/* Right: Issue List */}
        <section className={styles.feedbackPane}>
          <div className={styles.paneHeader}>
            <div className={styles.paneTitle}>
              <span className={`${styles.paneDot} ${styles.paneDotAccent}`} />
              <span>TUTOR FEEDBACK</span>
            </div>
            <div className={styles.shortcutHint}>
              <kbd>j</kbd>/<kbd>k</kbd> navigate · <kbd>↵</kbd> expand
            </div>
          </div>

          <div className={styles.issuePanelContainer}>
            <IssuePanel
              issues={issues}
              onLineClick={handleLineClick}
              onApplyFix={handleApplyFix}
              onInspect={(issue) => setInspectedIssue(issue)}
              fixedIssueIds={fixedIssueIds}
              activeLine={activeLine}
              filterSeverity={activeFilter}
            />
          </div>
        </section>
      </div>

      {/* ── Deep Dive Modal ── */}
      {inspectedIssue && (
        <IssueDetailModal
          issue={inspectedIssue}
          onClose={() => setInspectedIssue(null)}
          onApplyFix={handleApplyFix}
          isFixed={fixedIssueIds.has(inspectedIssue.id)}
        />
      )}

      {/* ── Toast Notification ── */}
      {toastMessage && (
        <div className={styles.toast} role="status">
          <Check size={14} className={styles.toastIcon} />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  )
}
