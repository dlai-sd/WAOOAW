/**
 * Auth Modal Component
 * Modal dialog for Google Sign-In with account selection
 */

import {
  Dialog,
  DialogSurface,
  DialogBody,
  DialogContent,
  makeStyles
} from '@fluentui/react-components'
import AuthPanel from './AuthPanel'
import { useState } from 'react'

const useStyles = makeStyles({
  surface: {
    padding: 0,
    maxHeight: '90vh',
    overflowY: 'auto',
    maxWidth: 'min(640px, calc(100vw - 24px))'
  },
  content: {
    padding: 0
  }
})

interface AuthModalProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
  theme?: 'light' | 'dark'
}

export default function AuthModal({ open, onClose, onSuccess, theme = 'light' }: AuthModalProps) {
  const styles = useStyles()

  const [panelKey, setPanelKey] = useState(0)

  const handleSuccess = () => {
    onClose()
    onSuccess?.()
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(_, data) => {
        if (!data.open) {
          setPanelKey((k) => k + 1)
          onClose()
        }
      }}
    >
      <DialogSurface className={styles.surface}>
        <DialogBody>
          <DialogContent className={styles.content}>
            <AuthPanel
              key={panelKey}
              theme={theme}
              showCloseButton
              onClose={() => {
                setPanelKey((k) => k + 1)
                onClose()
              }}
              onSuccess={() => {
                setPanelKey((k) => k + 1)
                onClose()
                onSuccess?.()
              }}
            />
          </DialogContent>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
