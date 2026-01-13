import { Card, CardHeader, Text, Body1, Button } from '@fluentui/react-components'
import { Certificate24Regular, BookOpen24Regular } from '@fluentui/react-icons'

export default function GenesisConsole() {
  const certificationQueue = [
    { id: 1, agentName: 'Marketing Agent Epsilon', skill: 'SEO Optimization', submittedBy: 'Agent Team' },
    { id: 2, agentName: 'Education Tutor Zeta', skill: 'Physics Teaching', submittedBy: 'Agent Team' },
    { id: 3, agentName: 'Sales SDR Theta', skill: 'Cold Calling', submittedBy: 'Agent Team' },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Genesis Console</Text>
        <Body1>Job/skill certification and agent capabilities</Body1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        <Card>
          <CardHeader 
            header={<Text weight="semibold">Certification Queue</Text>}
            description={<Text size={200}>{certificationQueue.length} pending</Text>}
          />
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {certificationQueue.map(item => (
              <Card key={item.id} appearance="outline">
                <div style={{ padding: '12px' }}>
                  <Text weight="semibold">{item.agentName}</Text>
                  <div style={{ marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Certificate24Regular fontSize={16} />
                    <Text size={200}>{item.skill}</Text>
                  </div>
                  <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                    <Button size="small" appearance="primary">Review</Button>
                    <Button size="small" appearance="subtle">Skip</Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader 
            header={<Text weight="semibold">Skill Library</Text>}
            description={<Text size={200}>47 certified skills</Text>}
          />
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen24Regular />
              <Text>Content Marketing (23 agents)</Text>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen24Regular />
              <Text>Math Tutoring (18 agents)</Text>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen24Regular />
              <Text>Lead Generation (12 agents)</Text>
            </div>
            <Button style={{ marginTop: '12px' }} appearance="subtle">View All Skills</Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
