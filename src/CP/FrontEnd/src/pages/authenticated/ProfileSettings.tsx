import { useEffect, useMemo, useState } from 'react'
import { Card } from '@fluentui/react-components'
import { getProfile, updateProfile, type ProfileData, type ProfileUpdatePayload } from '../../services/profile.service'

export default function ProfileSettings() {
  const [editOpen, setEditOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [form, setForm] = useState<ProfileUpdatePayload>({
    full_name: '',
    phone: '',
    business_name: '',
    industry: '',
  })
  const [saveStatus, setSaveStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setErrorMsg('')
      try {
        const data = await getProfile()
        if (cancelled) return
        setProfile(data)
        setForm({
          full_name: data.full_name || data.name || '',
          phone: data.phone || '',
          business_name: data.business_name || '',
          industry: data.industry || '',
        })
      } catch (e: any) {
        if (!cancelled) {
          setErrorMsg(e?.message || 'Failed to load profile. Please try again.')
          setProfile(null)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

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
      const updated = await updateProfile(payload)
      setProfile(updated)
      setForm({
        full_name: updated.full_name || updated.name || '',
        phone: updated.phone || '',
        business_name: updated.business_name || '',
        industry: updated.industry || '',
      })
      setSaveStatus('success')
      setEditOpen(false)
    } catch {
      setSaveStatus('error')
      setErrorMsg('Failed to save profile. Please try again.')
    }
  }

  const openSupport = () => {
    window.location.href = 'mailto:customersupport@dlaisd.com?subject=WAOOAW%20Customer%20Support'
  }

  const profileCompletion = useMemo(() => {
    const fields = [
      profile?.full_name || profile?.name,
      profile?.phone,
      profile?.business_name,
      profile?.industry,
    ]
    return fields.filter((value) => String(value || '').trim()).length
  }, [profile])

  const businessProfileStatus = loading
    ? 'Loading…'
    : profileCompletion >= 3
      ? 'Mostly configured'
      : profileCompletion > 0
        ? 'Needs review'
        : 'Action needed'

  const businessProfileNote = loading
    ? 'Loading your business profile'
    : profileCompletion >= 3
      ? 'Your business details are available to review and update here.'
      : 'Add or confirm your business details here.'

  const preferenceStatus = loading ? 'Loading…' : 'Available'
  const preferenceNote = loading
    ? 'Loading your available settings'
    : 'Review the settings currently available in your account.'

  const supportStatus = loading ? 'Loading…' : 'Available'
  const supportNote = loading
    ? 'Loading support options'
    : 'Open support and legal resources from here.'

  const sections = [
    {
      title: 'Account',
      icon: '👤',
      items: [
        { label: 'Edit Profile', action: handleEditClick, status: 'Available' },
        { label: 'Business Information', description: profile?.business_name ? `Current business: ${profile.business_name}` : 'Business details can be added here.', status: profile?.business_name ? 'Available' : 'Needs review' },
        { label: 'Team Members', description: 'Not available in this workspace yet.', status: 'Not available' },
      ],
    },
    {
      title: 'Preferences',
      icon: '⚙️',
      items: [
        { label: 'Notification Settings', description: 'Not available in this workspace yet.', status: 'Not available' },
        { label: 'Agent Preferences', description: 'Manage these inside each agent workspace.', status: 'Available elsewhere' },
        { label: 'Language & Region', description: 'Not available in this workspace yet.', status: 'Not available' },
      ],
    },
    {
      title: 'Support',
      icon: '💬',
      items: [
        { label: 'Contact Support', action: openSupport, status: 'Available' },
        { label: 'Help Center', description: 'Not available in this workspace yet.', status: 'Not available' },
        { label: 'Privacy Policy', description: 'Available from the public legal pages.', status: 'Available' },
        { label: 'Terms of Service', description: 'Available from the public legal pages.', status: 'Available' },
      ],
    },
  ]

  return (
    <div className="profile-settings-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h1>Profile & Settings</h1>
        <p style={{ color: 'var(--colorNeutralForeground2)', marginTop: '4px' }}>
          Manage your account details and available settings.
        </p>
      </div>

      <div className="profile-settings-hero">
        <Card className="profile-settings-hero-card profile-settings-hero-card--accent">
          <div className="profile-settings-hero-kicker">Workspace Identity</div>
          <h2>Keep your account details up to date.</h2>
          <p>
            Review your business information, available settings, and support options.
          </p>
        </Card>

        <div className="profile-settings-summary-grid">
          <Card className="profile-settings-summary-card">
            <div className="profile-settings-summary-label">Business profile</div>
            <div className="profile-settings-summary-value">{businessProfileStatus}</div>
            <div className="profile-settings-summary-note">{businessProfileNote}</div>
          </Card>
          <Card className="profile-settings-summary-card">
            <div className="profile-settings-summary-label">Preferences</div>
            <div className="profile-settings-summary-value">{preferenceStatus}</div>
            <div className="profile-settings-summary-note">{preferenceNote}</div>
          </Card>
          <Card className="profile-settings-summary-card">
            <div className="profile-settings-summary-label">Support routes</div>
            <div className="profile-settings-summary-value">{supportStatus}</div>
            <div className="profile-settings-summary-note">{supportNote}</div>
          </Card>
        </div>
      </div>

      {loading && (
        <Card style={{ padding: '16px', marginBottom: '16px' }}>
          Loading your current profile.
        </Card>
      )}

      {!loading && errorMsg && (
        <Card style={{ padding: '16px', marginBottom: '16px', color: 'var(--colorStatusDangerForeground1)' }}>
          {errorMsg}
        </Card>
      )}

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
          <Card style={{ padding: '28px', minWidth: 0, maxWidth: '480px', width: 'min(100%, 480px)', boxSizing: 'border-box' }}>
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))', gap: '16px' }}>
        {sections.map((section) => (
          <Card key={section.title} className="profile-settings-section-card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <span style={{ fontSize: '24px' }}>{section.icon}</span>
              <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>{section.title}</h2>
            </div>
            <p style={{ color: 'var(--colorNeutralForeground2)', marginBottom: '14px', fontSize: '13px' }}>
              {section.title === 'Account' && 'View and update your account details.'}
              {section.title === 'Preferences' && 'Review the settings currently available in CP.'}
              {section.title === 'Support' && 'Open support and legal resources.'}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {section.items.map((item) => (
                <button
                  key={item.label}
                  onClick={item.action}
                  disabled={!item.action}
                  style={{
                    textAlign: 'left',
                    padding: '10px 12px',
                    border: '1px solid var(--colorNeutralStroke2)',
                    borderRadius: '6px',
                    background: 'var(--colorNeutralBackground1)',
                    color: 'var(--colorNeutralForeground1)',
                    cursor: item.action ? 'pointer' : 'default',
                    fontSize: '14px',
                    transition: 'background 0.15s',
                    opacity: item.action ? 1 : 0.88,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center' }}>
                    <span>{item.label}</span>
                    <span style={{ fontSize: '12px', color: 'var(--colorNeutralForeground2)' }}>{item.status}</span>
                  </div>
                  {item.description && (
                    <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--colorNeutralForeground2)' }}>
                      {item.description}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
