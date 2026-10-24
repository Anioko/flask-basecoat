"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Sidebar } from "./components/sidebar";
import { Content } from "./components/content";

const onboardingSteps = [
  {
    id: "role",
    title: "Role & Use Case",
    completed: false,
    current: true
  },
  {
    id: "template",
    title: "Choose a Template or Start from Scratch",
    completed: false,
    current: false
  },
  {
    id: "data-source",
    title: "Data Source Setup",
    completed: false,
    current: false
  },
  {
    id: "first-flow",
    title: "Build Your First Flow",
    completed: false,
    current: false,
    optional: true
  },
  {
    id: "invite-team",
    title: "Invite Team",
    completed: false,
    current: false,
    optional: true
  }
];

export default function Page() {
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState(onboardingSteps);

  const handleContinue = (data: { role: string; automation: string[] }) => {
    console.log("Onboarding data:", data);

    // Mark current step as completed and move to next
    const newSteps = steps.map((step, index) => {
      if (index === currentStep) {
        return { ...step, completed: true, current: false };
      }
      if (index === currentStep + 1) {
        return { ...step, current: true };
      }
      return step;
    });

    setSteps(newSteps);
    setCurrentStep(currentStep + 1);
  };

  return (
    <div className="flex min-h-screen overflow-hidden">
      <div className="hidden lg:block">
        <Sidebar steps={steps} />
      </div>

      <Content onContinue={handleContinue} />

      <div className="border-onboarding-option-border fixed right-0 bottom-0 left-0 border-t p-4 lg:hidden">
        <div className="flex items-center justify-center gap-2">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                "h-2 w-2 rounded-full transition-colors",
                step.completed
                  ? "bg-accent"
                  : step.current
                    ? "bg-primary"
                    : "bg-onboarding-option-border"
              )}
            />
          ))}
        </div>
        <div className="mt-2 text-center">
          <span className="text-onboarding-text-muted font-inter text-sm">
            Step {currentStep + 1} of {steps.length}
          </span>
        </div>
      </div>
    </div>
  );
}
