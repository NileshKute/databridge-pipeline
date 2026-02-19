import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

interface Props {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: LucideIcon;
}

export default function EmptyState({ title, description, action, icon: Icon = Inbox }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon className="h-12 w-12 text-surface-500 mb-4" />
      <h3 className="text-lg font-medium text-surface-300 mb-1">{title}</h3>
      {description && <p className="text-surface-400 text-sm mb-4">{description}</p>}
      {action}
    </div>
  );
}
