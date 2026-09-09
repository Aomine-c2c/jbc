import JobCardDetailClient from "./JobCardDetailClient";

export function generateStaticParams() {
  return [{ id: "default" }];
}

export default function JobCardDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <JobCardDetailClient params={params} />;
}
