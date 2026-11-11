import { MessageSquare } from 'lucide-react';
import { ComingSoon } from '../components';

export default function ChatPage() {
  return (
    <ComingSoon
      title="AI Chat"
      description="Ask questions about your medical reports and receive educational explanations powered by trusted medical sources."
      phase={9}
      icon={<MessageSquare size={32} />}
      features={[
        'Natural language questions about your reports',
        'Streaming AI responses for fast feedback',
        'Clear separation of report facts vs general knowledge',
        'Citations linking to trusted medical sources',
        'Medical terminology explanations on hover',
        'Conversation history and context awareness',
        'Suggested follow-up questions',
        'Feedback to improve AI responses',
      ]}
    />
  );
}
