import { clsx } from "clsx";

interface PipelineStep {
  emoji: string;
  label: string;
  color: string;
}

const STEPS: PipelineStep[] = [
  { emoji: "📤", label: "Artist Upload", color: "border-cyan-500 bg-cyan-950/40" },
  { emoji: "👥", label: "Team Lead", color: "border-amber-500 bg-amber-950/40" },
  { emoji: "🎬", label: "Supervisor", color: "border-amber-500 bg-amber-950/40" },
  { emoji: "💰", label: "Line Producer", color: "border-violet-500 bg-violet-950/40" },
  { emoji: "🔍", label: "Data Team Scan", color: "border-blue-500 bg-blue-950/40" },
  { emoji: "🚀", label: "IT Transfer", color: "border-rose-500 bg-rose-950/40" },
  { emoji: "✅", label: "Production", color: "border-emerald-500 bg-emerald-950/40" },
];

export default function PipelineVisual() {
  return (
    <div className="bg-bg-card border border-surface-700 rounded-xl p-6">
      <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-6">
        Pipeline Flow
      </h3>
      <div className="flex items-center justify-between overflow-x-auto pb-2">
        {STEPS.map((step, i) => (
          <div key={step.label} className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center gap-2">
              <div
                className={clsx(
                  "w-12 h-12 rounded-full border-2 flex items-center justify-center text-lg",
                  step.color,
                )}
              >
                {step.emoji}
              </div>
              <span className="text-[11px] text-text-muted text-center whitespace-nowrap font-medium">
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className="flex items-center mx-2 -mt-5">
                <div className="w-8 sm:w-12 lg:w-16 h-px bg-gradient-to-r from-surface-600 to-surface-500" />
                <div className="w-0 h-0 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent border-l-[6px] border-l-surface-500 -ml-px" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
