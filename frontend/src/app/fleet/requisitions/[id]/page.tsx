import RequisitionDetailClient from "./RequisitionDetailClient";

export default function RequisitionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <RequisitionDetailClient params={params} />;
}
