import { useState } from 'react'
import { Card } from '@fluentui/react-components'
import { updateProfile, type ProfileUpdatePayload } from '../../services/profile.service'

export default function ProfileSettings() {
  const [editOpen, setEditOpen] = useState(false)
  const [form, setForm] = useState<ProfileUpdatePayload>({
    full_name: '',
    phone: '',
    business_name: '',
    industry: '',
  })
  const [saveStatus, setSaveStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleEditClick = () => {
    setSaveStatus('idle')
    setErrorMsg('')
    setEditOpen(true)
  }

  const handleFormChange = (field: keyof ProfileUpdatePayload, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    setSaveStatus('loading')
    setErrorMsg('')
    try {
      const payload: ProfileUpdatePayload = {}
      if (form.full_name?.trim()) payload.full_name = form.full_name.trim()
      if (form.phone?.trim()) payload.phone = form.phone.trim()
      if (form.business_name?.trim()) payload.business_name = form.business_name.trim()
      if (form.industry?.trim()) payload.industry = form.industry.trim()
      await updateProfile(payload)
      setSaveStatus('success')
      setEditOpen(false)
    } catch {
      setSaveStatus('error')
      setErrorMsg('Failed to save profile. Please try again.')
    }
  }

  const sections = [
    {
      title: 'Account',
      icon: '👤',
      items: ['Edit Profile', 'Business Information', 'Team Members'],
    },
    {
      title: 'Preferences',
      icon: '⚙️',
      items: ['Notification Settings', 'Agent Preferences', 'Language & Region'],
    },
    {
      title: 'Support',
      icon: '💬',
      items: ['Help Center', 'Contact Support', 'Privacy Policy', 'Terms of Service'],
    },
  ]

  return (
    <div className="profile-settings-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Profile & Settings</h1>
        <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
          Manage your business identity, team members, and preferences.
        </p>
      </div>

      <div className="profile-settings-hero">
        <Card className="profile-settings-hero-card profile-settings-hero-card--accent">
          <div className="profile-settings-hero-kicker">Workspace Identity</div>
          <h2>Keep your account aligned with how WAOOAW works for your business.</h2>
          <p>
            Customers should feel that their profile is the operating brief for their agent workforce,
            not just a settings form hidden after signup.
          </p>
        </Card>

        <div className="profile-settings-summary-grid">
          <Card className="profile-settings-summary-card">
            <div className="profile-settings-summary-label">Business profile</div>
            <div className="profile-settings-summary-value">Ready</div>
            <div className="profile-settings-summary-note">Name, phone, and company details are editable here.</div>
          </Card>
          <Card className="profile-settings-summary-card">
            <div className="profile-settings-summary-label">Preferences</div>
            <div className="profile-settings-summary-value">In control</div>
            <div className="profile-settings-summary-note">Notification, language, and operating preferences live in one place.</div>
          </Card>
          <Card className="profile-settings-summary-card">
            <div className="profile-settings-summary-label">Support routes</div>
            <div className="profile-settings-summary-value">Always visible</div>
            <div className="profile-settings-summary-note">Help, privacy, and support should never feel hidden during a live issue.</div>
          </Card>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {editOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          role="dialog"
          aria-modal="true"
          aria-label="Edit Profile"
        >
          <Card style={{ padding: '28px', minWidth: '340px', maxWidth: '480px', width: '100%' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '20px' }}>Edit Profile</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {[
                { label: 'Full Name', field: 'full_name' as const, type: 'text', placeholder: 'Your full name' },
                { label: 'Phone', field: 'phone' as const, type: 'tel', placeholder: '+91 98765 43210' },
                { label: 'Business Name', field: 'business_name' as const, type: 'text', placeholder: 'Your company' },
                { label: 'Industry', field: 'industry' as const, type: 'text', placeholder: 'e.g. marketing, education' },
              ].map(({ label, field, type, placeholder }) => (
                <div key={field}>
                  <label
                    htmlFor={`profile-field-${field}`}
                    style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}
                  >
                    {label}
                  </label>
                  <input
                    id={`profile-field-${field}`}
                    type={type}
                    placeholder={placeholder}
                    value={form[field] ?? ''}
                    onChange={(e) => handleFormChange(field, e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      border: '1px solid var(--colorNeutralStroke2)',
                      borderRadius: '6px',
                      background: 'var(--colorNeutralBackground1)',
                      color: 'var(--colorNeutralForeground1)',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              ))}
            </div>

            {saveStatus === 'error' && (
              <p style={{ color: 'var(--colorStatusDangerForeground1)', marginTop: '10px', fontSize: '13px' }}>
                {errorMsg}
              </p>
            )}

            <div style={{ display: 'flex', gap: '10px', marginTop: '20px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditOpen(false)}
                disabled={saveStatus === 'loading'}
                style={{
                  padding: '8px 18px',
                  border: '1px solid var(--colorNeutralStroke2)',
                  borderRadius: '6px',
                  background: 'transparent',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saveStatus === 'loading'}
                style={{
                  padding: '8px 18px',
                  border: 'none',
                  borderRadius: '6px',
                  background: 'var(--colorBrandBackground)',
                  color: '#fff',
                  cursor: saveStatus === 'loading' ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: 600,
                }}
              >
                {saveStatus === 'loading' ? 'Saving…' : 'Save'}
              </button>
            </div>
          </Card>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {sections.map((section) => (
          <Card key={section.title} className="profile-settings-section-card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <span style={{ fontSize: '24px' }}>{section.icon}</span>
              <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>{section.title}</h2>
            </div>
            <p style={{ color: 'var(--colorNeutralForeground2)', marginBottom: '14px', fontSize: '13px' }}>
              {section.title === 'Account' && 'Identity, team readiness, and business context that power your hires.'}
              {section.title === 'Preferences' && 'Tune how WAOOAW alerts you, how agents behave, and what operational defaults matter.'}
              {section.title === 'Support' && 'Reach the help, policy, and trust surfaces customers need when something feels unclear.'}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {section.items.map((item) => (
                <button
                  key={item}
                  onClick={item === 'Edit Profile' ? handleEditClick : undefined}
                  style={{
                    textAlign: 'left',
                    padding: '10px 12px',
                    border: '1px solid var(--colorNeutralStroke2)',
                    borderRadius: '6px',
                    background: 'var(--colorNeutralBackground1)',
                    color: 'var(--colorNeutralForeground1)',
                    cursor: 'pointer',
                    fontSize: '14px',
                    transition: 'background 0.15s',
                  }}
                >
                  {item}
                </button>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
