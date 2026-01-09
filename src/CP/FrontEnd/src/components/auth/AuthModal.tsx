/**
 * Auth Modal Component
 * Modal dialog for Google Sign-In with account selection
 */

import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent,
  Button,
  makeStyles
} from '@fluentui/react-components'
import { Dismiss24Regular } from '@fluentui/react-icons'
import GoogleLoginButton from './GoogleLoginButton'

const useStyles = makeStyles({
  surface: {
    maxWidth: '450px',
    padding: '32px',
    borderRadius: '16px'
  },
  surfaceDark: {
    backgroundColor: '#18181b',
    border: '1px solid rgba(0, 242, 254, 0.2)',
    boxShadow: '0 0 40px rgba(0, 242, 254, 0.15), 0 20px 60px rgba(0, 0, 0, 0.5)'
  },
  surfaceLight: {
    backgroundColor: '#ffffff',
    border: '1px solid rgba(102, 126, 234, 0.2)',
    boxShadow: '0 0 40px rgba(102, 126, 234, 0.1), 0 20px 60px rgba(0, 0, 0, 0.1)'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '28px',
    paddingBottom: '20px'
  },
  headerDark: {
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
  },
  headerLight: {
    borderBottom: '1px solid rgba(0, 0, 0, 0.1)'
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #00f2fe 0%, #667eea 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    margin: '0',
    fontFamily: "'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    letterSpacing: '-0.02em'
  },
  closeButton: {
    color: '#a1a1aa',
    transition: 'all 0.2s ease',
    ':hover': {
      color: '#00f2fe',
      backgroundColor: 'rgba(0, 242, 254, 0.1)',
      boxShadow: '0 0 20px rgba(0, 242, 254, 0.3)'
    }
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '28px',
    alignItems: 'center',
    padding: '20px 0'
  },
  subtitle: {
    textAlign: 'center',
    color: '#d4d4d8',
    marginBottom: '10px',
    lineHeight: '1.6'
  },
  subtitleStrong: {
    fontSize: '18px',
    fontWeight: '600'
  },
  subtitleStrongDark: {
    color: '#f5f5f5'
  },
  subtitleStrongLight: {
    color: '#18181b'
  },
  subtitleDark: {
    color: '#d4d4d8'
  },
  subtitleLight: {
    color: '#52525b'
  },
  logo: {
    fontSize: '56px',
    marginBottom: '10px',
    filter: 'drop-shadow(0 0 10px rgba(0, 242, 254, 0.3))'
  },
  divider: {
    width: '100%',
    height: '1px',
    background: 'linear-gradient(90deg, transparent 0%, rgba(0, 242, 254, 0.3) 50%, transparent 100%)',
    margin: '24px 0'
  },
  footer: {
    textAlign: 'center',
    fontSize: '11px',
    marginTop: '24px',
    lineHeight: '1.5'
  },
  footerDark: {
    color: '#71717a'
  },
  footerLight: {
    color: '#a1a1aa'
  }
})

interface AuthModalProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
  theme?: 'light' | 'dark'
}

export default function AuthModal({ open, onClose, onSuccess, theme = 'light' }: AuthModalProps) {
  const isDark = theme === 'dark'
  const styles = useStyles()

  const handleSuccess = () => {
    onClose()
    onSuccess?.()
  }

  const handleError = (error: string) => {
    console.error('Auth error:', error)
  }

  return (
    <Dialog open={open} onOpenChange={(_, data) => !data.open && onClose()}>
      <DialogSurface className={`${styles.surface} ${isDark ? styles.surfaceDark : styles.surfaceLight}`}>
        <DialogBody>
          <div className={`${styles.header} ${isDark ? styles.headerDark : styles.headerLight}`}>
            <DialogTitle className={styles.title}>
              Sign in to WAOOAW
            </DialogTitle>
            <Button
              appearance="subtle"
              icon={<Dismiss24Regular />}
              onClick={onClose}
              className={styles.closeButton}
            />
          </div>
          
          <DialogContent className={styles.content}>
            <div className={styles.logo}>👋</div>
            
            <div className={`${styles.subtitle} ${isDark ? styles.subtitleDark : styles.subtitleLight}`}>
              <strong className={`${styles.subtitleStrong} ${isDark ? styles.subtitleStrongDark : styles.subtitleStrongLight}`}>Welcome to WAOOAW</strong>
              <br />
              Agents that make you say WOW!
            </div>

            <GoogleLoginButton onSuccess={handleSuccess} onError={handleError} />

            <div className={`${styles.footer} ${isDark ? styles.footerDark : styles.footerLight}`}>
              By signing in, you agree to our Terms of Service and Privacy Policy
            </div>
          </DialogContent>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
