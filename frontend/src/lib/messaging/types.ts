export interface ConversationMemberInfo {
  user_id: string;
  full_name: string;
}

export interface Conversation {
  id: string;
  type: "direct" | "channel";
  name: string | null;
  members: ConversationMemberInfo[];
  last_message_preview: string | null;
  last_message_at: string | null;
  unread_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name: string;
  body: string;
  created_at: string;
}
