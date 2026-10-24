import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ChevronRightIcon } from "lucide-react";

interface OnboardingContentProps {
  onContinue: (data: { role: string; automation: string[] }) => void;
}

const roles = [
  { id: "product-manager", label: "Product Manager" },
  { id: "developer", label: "Developer" },
  { id: "designer", label: "Designer" },
  { id: "ops", label: "Ops" },
  { id: "founder", label: "Founder" },
  { id: "other", label: "Other" }
];

const automationOptions = [
  { id: "data-collection", label: "Data collection & processing" },
  { id: "emails", label: "Sending emails or messages" },
  { id: "dashboard", label: "Dashboard updates" },
  { id: "repetitive-tasks", label: "Repetitive internal tasks" },
  { id: "ai-assistant", label: "Building your own AI assistant" },
  { id: "other", label: "Other" }
];

export const Content = ({ onContinue }: OnboardingContentProps) => {
  const [selectedRole, setSelectedRole] = useState("product-manager");
  const [selectedAutomation, setSelectedAutomation] = useState<string[]>([
    "data-collection",
    "repetitive-tasks"
  ]);

  const toggleAutomation = (option: string) => {
    setSelectedAutomation((prev) =>
      prev.includes(option) ? prev.filter((item) => item !== option) : [...prev, option]
    );
  };

  const handleContinue = () => {
    onContinue({
      role: selectedRole,
      automation: selectedAutomation
    });
  };

  return (
    <div className="min-h-screen flex-1 p-8 lg:p-16">
      <div className="mx-auto max-w-xl">
        {/* Header */}
        <div className="mb-16">
          <h1 className="text-foreground mb-4 text-3xl leading-tight font-semibold lg:text-4xl">
            Let&#39;s personalize your experience
          </h1>
          <p className="text-muted-foreground leading-relaxed">
            Tell us a bit about you so we can tailor templates, suggestions, and features to your
            needs.
          </p>
        </div>

        {/* Role Selection */}
        <div className="mb-12">
          <h4 className="text-foreground mb-8 text-xl">What best describes your role?</h4>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            {roles.map((role) => (
              <button
                key={role.id}
                onClick={() => setSelectedRole(role.id)}
                className={cn(
                  "font-inter rounded-lg border p-4 text-left font-medium transition-all duration-200 hover:shadow-sm",
                  selectedRole === role.id
                    ? "border-gray-700"
                    : "border-onboarding-option-border text-foreground hover:border-onboarding-option-border/60"
                )}>
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      selectedRole === role.id ? "bg-green-400" : "bg-onboarding-option-border"
                    )}></div>
                  {role.label}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Automation Selection */}
        <div className="mb-16">
          <h4 className="text-foreground mb-8 text-xl">What do you want to automate first?</h4>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {automationOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => toggleAutomation(option.id)}
                className={cn(
                  "font-inter rounded-lg border p-4 text-left font-medium transition-all duration-200 hover:shadow-sm",
                  selectedAutomation.includes(option.id)
                    ? "border-gray-700"
                    : "border-onboarding-option-border text-foreground hover:border-onboarding-option-border/60"
                )}>
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      selectedAutomation.includes(option.id)
                        ? "bg-green-400"
                        : "bg-onboarding-option-border"
                    )}></div>
                  {option.label}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-center">
          <Button onClick={handleContinue} className="flex w-full justify-between" size="lg">
            Continue
            <ChevronRightIcon />
          </Button>
        </div>
      </div>
    </div>
  );
};
