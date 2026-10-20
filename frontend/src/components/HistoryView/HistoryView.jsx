import { useState } from 'react'
import {
  Search,
  Download,
  ExternalLink,
  FileCode,
  Calendar,
  CheckCircle2,
  Trash2,
} from 'lucide-react'
import { SeverityIcon } from '../IssuePanel/IssuePanel'
import styles from './HistoryView.module.css'

export default function HistoryView({
  history = [],
  onSelectReview,
  onClearHistory,
}) {
  const [search, setSearch] = useState('')
  const [langFilter, setLangFilter] = useState('all')

  const filtered = history.filter((item) => {
    const matchesSearch =
      item.filename.toLowerCase().includes(search.toLowerCase()) ||
      item.language.toLowerCase().includes(search.toLowerCase())
    const matchesLang =
      langFilter === 'all' || item.language.toLowerCase() === langFilter
    return matchesSearch && matchesLang
  })

  function exportSingleJson(item) {
    const blob = new Blob([JSON.stringify(item, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${item.filename}_review.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function exportAllJson() {
    const blob = new Blob([JSON.stringify(history, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `codetutor_history_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.container}>
      {/* ── Header Bar ── */}
      <div className={styles.topBar}>
        <div>
          <h1 className={styles.title}>Review History</h1>
          <p className={styles.subtitle}>
            Audit log of past student submissions, issue detections, and automated tutoring reports.
          </p>
        </div>

        <div className={styles.topActions}>
          {history.length > 0 && (
            <>
              <button
                className={styles.secondaryBtn}
                onClick={exportAllJson}
                title="Download all past reviews as JSON"
              >
                <Download size={14} />
                <span>Export All (JSON)</span>
              </button>

              {onClearHistory && (
                <button
                  className={styles.ghostBtn}
                  onClick={onClearHistory}
                  title="Clear history"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Filter Bar ── */}
      <div className={styles.filterBar}>
        <div className={styles.searchBox}>
          <Search size={14} className={styles.searchIcon} />
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Search by file or language…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className={styles.langFilters}>
          {['all', 'python', 'java'].map((lang) => (
            <button
              key={lang}
              className={`${styles.filterBtn} ${langFilter === lang ? styles.filterBtnActive : ''}`}
              onClick={() => setLangFilter(lang)}
            >
              {lang === 'all' ? 'All Languages' : lang.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* ── History Table ── */}
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.thFile}>FILE</th>
              <th className={styles.thLang}>LANGUAGE</th>
              <th className={styles.thIssues}>ISSUES DETECTED</th>
              <th className={styles.thDate}>REVIEWED AT</th>
              <th className={styles.thActions}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className={styles.emptyCell}>
                  <div className={styles.emptyState}>
                    <FileCode size={24} className={styles.emptyIcon} />
                    <p className={styles.emptyTitle}>No review records match criteria</p>
                    <p className={styles.emptySub}>
                      Submit a code snippet or clear your search filters.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const counts = item.severityCounts || {}
                const hasIssues = item.issueCount > 0

                return (
                  <tr key={item.id} className={styles.row}>
                    <td className={styles.tdFile}>
                      <div className={styles.fileCell}>
                        <FileCode size={14} className={styles.rowFileIcon} />
                        <span className={styles.rowFileName}>{item.filename}</span>
                      </div>
                    </td>

                    <td className={styles.tdLang}>
                      <span className={styles.langBadge}>
                        {item.language.toUpperCase()}
                      </span>
                    </td>

                    <td className={styles.tdIssues}>
                      {hasIssues ? (
                        <div className={styles.issueBreakdown}>
                          <span className={styles.totalBadge}>{item.issueCount} total</span>
                          {counts.error > 0 && (
                            <span className={styles.breakdownChip} title="Errors">
                              <SeverityIcon severity="error" size={10} />
                              <span>{counts.error}</span>
                            </span>
                          )}
                          {counts.warning > 0 && (
                            <span className={styles.breakdownChip} title="Warnings">
                              <SeverityIcon severity="warning" size={10} />
                              <span>{counts.warning}</span>
                            </span>
                          )}
                          {counts.info > 0 && (
                            <span className={styles.breakdownChip} title="Info / Performance">
                              <SeverityIcon severity="info" size={10} />
                              <span>{counts.info}</span>
                            </span>
                          )}
                          {counts.style > 0 && (
                            <span className={styles.breakdownChip} title="Style">
                              <SeverityIcon severity="style" size={10} />
                              <span>{counts.style}</span>
                            </span>
                          )}
                        </div>
                      ) : (
                        <div className={styles.cleanBadge}>
                          <CheckCircle2 size={13} className={styles.cleanIcon} />
                          <span>0 issues · Clean code</span>
                        </div>
                      )}
                    </td>

                    <td className={styles.tdDate}>
                      <div className={styles.dateCell}>
                        <Calendar size={12} className={styles.dateIcon} />
                        <span>
                          {new Date(item.date).toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </td>

                    <td className={styles.tdActions}>
                      <div className={styles.actionsGroup}>
                        <button
                          className={styles.openBtn}
                          onClick={() => onSelectReview(item)}
                          title="Open in Code Review screen"
                        >
                          <span>Open</span>
                          <ExternalLink size={12} />
                        </button>

                        <button
                          className={styles.jsonBtn}
                          onClick={() => exportSingleJson(item)}
                          title="Export single review JSON"
                        >
                          <Download size={12} />
                          <span>JSON</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
