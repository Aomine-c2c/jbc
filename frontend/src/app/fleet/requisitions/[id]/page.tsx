import RequisitionDetailClient from "./RequisitionDetailClient";

export function generateStaticParams() {
  return [{ id: "default" }];
}

export default function RequisitionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <RequisitionDetailClient params={params} />;
}
