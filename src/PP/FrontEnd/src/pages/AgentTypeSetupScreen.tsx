import AgentSetupStudio from './AgentSetupStudio'

interface AgentTypeSetupScreenProps {
  agentSetupId?: string
}

export default function AgentTypeSetupScreen({ agentSetupId }: AgentTypeSetupScreenProps) {
  return <AgentSetupStudio agentSetupId={agentSetupId} />
}
