import { cn } from "@/lib/utils";
import { BoxIcon } from "lucide-react";

interface OnboardingStep {
  id: string;
  title: string;
  completed: boolean;
  current: boolean;
  optional?: boolean;
}

interface OnboardingSidebarProps {
  steps: OnboardingStep[];
  className?: string;
}

export const Sidebar = ({ steps, className }: OnboardingSidebarProps) => {
  return (
    <div
      className={cn(
        "relative flex min-h-screen w-80 flex-col bg-gradient-to-b from-black to-indigo-700 p-6 text-white",
        className
      )}>
      <div className="mb-12 flex items-center gap-3 pt-4">
        <BoxIcon className="size-6" />
      </div>

      {/* Steps */}
      <div className="flex-1 space-y-4">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={cn(
              "flex items-center gap-4 rounded-lg p-3 transition-all duration-200",
              step.current && "bg-white/10"
            )}>
            <div
              className={cn(
                "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border-2",
                step.completed
                  ? "border-green-400 bg-green-400"
                  : step.current
                    ? "border-white bg-transparent"
                    : "border-white/30"
              )}>
              {step.completed ? (
                <svg className="h-3 w-3 text-gray-800" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : step.current ? (
                <div className="h-2 w-2 rounded-full bg-white"></div>
              ) : (
                <span className="text-xs text-white/60">{index + 1}</span>
              )}
            </div>
            <div className="flex-1">
              <div
                className={cn(
                  "font-inter text-sm font-medium",
                  step.current ? "text-white" : "text-white/70"
                )}>
                {step.title}
              </div>
              {step.optional && <div className="font-inter text-xs text-white/50">optional</div>}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="font-inter mt-auto flex justify-between pt-8 text-sm text-white/60">
        <span>Terms of Service</span>
        <span>Help Center</span>
      </div>
    </div>
  );
};
