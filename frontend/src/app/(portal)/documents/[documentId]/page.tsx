import { DocumentDetailClient } from "./document-detail-client";

export default async function DocumentDetailPage({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  return <DocumentDetailClient documentId={documentId} />;
}
