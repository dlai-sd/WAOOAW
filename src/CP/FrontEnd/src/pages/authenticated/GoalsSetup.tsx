import { Card, Button, Textarea } from '@fluentui/react-components'

export default function GoalsSetup() {
  return (
    <div className="goals-setup-page">
      <div className="page-header">
        <h1>Configure Goals for: Content Marketing Agent</h1>
        <div>
          <Button appearance="outline">Save Draft</Button>
          <Button appearance="primary">Submit for Genesis Validation</Button>
        </div>
      </div>

      <Card className="wizard-card">
        <h2>Wizard: Step 1/5 - Goal Statement</h2>
        
        <div className="form-group">
          <label>Primary Goal *</label>
          <Textarea 
            placeholder="Publish 5 HIPAA-compliant blog posts per week about diabetes management"
            rows={4}
          />
          <div className="character-count">Character count: 85/500</div>
        </div>

        <div className="form-group">
          <label>Use Template:</label>
          <div className="template-buttons">
            <Button appearance="outline">Healthcare Content</Button>
            <Button appearance="outline">Marketing Campaign</Button>
            <Button appearance="outline">Sales</Button>
          </div>
        </div>

        <div className="form-group">
          <label>Priority Level:</label>
          <div className="radio-group">
            <label><input type="radio" name="priority" /> P0 Critical</label>
            <label><input type="radio" name="priority" defaultChecked /> P1 High</label>
            <label><input type="radio" name="priority" /> P2 Medium</label>
            <label><input type="radio" name="priority" /> P3 Low</label>
          </div>
        </div>

        <div className="form-group">
          <label>Timeline:</label>
          <div className="radio-group">
            <label><input type="radio" name="timeline" /> Immediate</label>
            <label><input type="radio" name="timeline" defaultChecked /> Weekly</label>
            <label><input type="radio" name="timeline" /> Monthly</label>
          </div>
        </div>

        <div className="wizard-nav">
          <Button appearance="outline">← Back</Button>
          <Button appearance="primary">Next: Criteria →</Button>
        </div>
      </Card>

      <section className="existing-goals">
        <h2>Existing Goals (3)</h2>
        <Card className="goal-item">
          <div className="goal-header">
            <span>✅ Goal 1: Publish 5 blog posts/week</span>
            <span>[P1] [Active]</span>
          </div>
          <div className="goal-status">
            Status: 3/5 complete this week (60%)
          </div>
          <Button appearance="subtle">Edit</Button>
        </Card>
      </section>
    </div>
  )
}
