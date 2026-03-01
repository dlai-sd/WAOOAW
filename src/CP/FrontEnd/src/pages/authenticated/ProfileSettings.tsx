import { Card } from '@fluentui/react-components'

export default function ProfileSettings() {
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {sections.map((section) => (
          <Card key={section.title} style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <span style={{ fontSize: '24px' }}>{section.icon}</span>
              <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>{section.title}</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {section.items.map((item) => (
                <button
                  key={item}
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
