export interface Comment {
  id: string;
  document_id: string;
  parent_comment_id: string | null;
  author_id: string;
  author_name: string;
  body: string;
  is_edited: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  mentioned_user_ids: string[];
}
