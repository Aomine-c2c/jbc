import JobCardDetailClient from "./JobCardDetailClient";

export default function JobCardDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <JobCardDetailClient params={params} />;
}
