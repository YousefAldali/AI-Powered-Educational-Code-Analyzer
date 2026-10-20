import { useState, useEffect } from 'react'
import {
  Sun,
  Moon,
  Code2,
  FileText,
  Clock,
  Sparkles,
  Layers,
  BarChart2,
} from 'lucide-react'
import styles from './Header.module.css'

export default function Header({
  activeTab,
  onTabChange,
  activeLanguage,
  onLanguageChange,
}) {
  const [theme, setTheme] = useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'light'
  })

  useEffect(() => {
    const saved = localStorage.getItem('codetutor-theme')
    if (saved) {
      setTheme(saved)
      document.documentElement.setAttribute('data-theme', saved)
    }
  }, [])

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    document.documentElement.setAttribute('data-theme', next)
    localStorage.setItem('codetutor-theme', next)
  }

  const navItems = [
    { id: 'review', label: 'Review Results', icon: Code2, badge: 'Hero' },
    { id: 'submit', label: 'Submit Code', icon: FileText },
    { id: 'history', label: 'History', icon: Clock },
    { id: 'coaching', label: 'Live Coach', icon: Sparkles, badge: 'Stretch' },
    { id: 'states', label: 'States', icon: Layers },
    { id: 'dashboard', label: 'Evaluation', icon: BarChart2 },
  ]

  return (
    <header className={styles.header}>
      {/* ── Left: Brand Identity ── */}
      <div className={styles.brandArea}>
        <div className={styles.brandLogo}>
          <div className={styles.logoMark} aria-hidden="true">
            <span className={styles.logoGlyph}>◈</span>
          </div>
          <span className={styles.brandTitle}>CodeTutor</span>
        </div>
        <span className={styles.academicBadge}>Academic Edition</span>
      </div>

      {/* ── Center: Primary Navigation Tabs ── */}
      <nav className={styles.nav} aria-label="Main Navigation">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              className={`${styles.navTab} ${isActive ? styles.navTabActive : ''}`}
              onClick={() => onTabChange(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={14} className={styles.tabIcon} />
              <span>{item.label}</span>
              {item.badge && <span className={styles.tabBadge}>{item.badge}</span>}
            </button>
          )
        })}
      </nav>

      {/* ── Right: Language & Theme Controls ── */}
      <div className={styles.controlsArea}>
        {/* Language selector */}
        {onLanguageChange && (
          <div className={styles.langPills} role="group" aria-label="Target language">
            {['python', 'java'].map((lang) => (
              <button
                key={lang}
                className={`${styles.langPill} ${activeLanguage === lang ? styles.langPillActive : ''}`}
                onClick={() => onLanguageChange(lang)}
              >
                {lang === 'python' ? 'Python' : 'Java'}
              </button>
            ))}
          </div>
        )}

        <div className={styles.divider} />

        {/* Theme Toggle */}
        <button
          className={styles.themeToggle}
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to Light mode' : 'Switch to Dark mode'}
          aria-label="Toggle color theme"
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  )
}
