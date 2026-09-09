import MachineDetailClient from "./MachineDetailClient";

export function generateStaticParams() {
  return [{ id: "default" }];
}

export default function MachineDetailPage() {
  return <MachineDetailClient />;
}
