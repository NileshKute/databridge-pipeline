import { useParams } from "react-router-dom";
import PageHeader from "@/components/common/PageHeader";

export default function TransferDetailPage() {
  const { id } = useParams();
  return (
    <div>
      <PageHeader title={`Transfer #${id}`} subtitle="Transfer details and history" />
      <div className="card">
        <p className="text-text-secondary">Transfer detail view will be implemented in the next module.</p>
      </div>
    </div>
  );
}
