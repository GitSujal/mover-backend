import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface WizardStepperProps {
    currentStep: number;
    steps: string[];
}

export function WizardStepper({ currentStep, steps }: WizardStepperProps) {
    return (
        <nav aria-label="Progress">
            <ol role="list" className="flex items-center">
                {steps.map((step, index) => {
                    const stepNumber = index + 1;
                    const isCompleted = stepNumber < currentStep;
                    const isCurrent = stepNumber === currentStep;

                    return (
                        <li key={step} className={cn(index !== steps.length - 1 ? "pr-8 sm:pr-20" : "", "relative")}>
                            {index !== steps.length - 1 && (
                                <div
                                    className="absolute top-4 left-0 -ml-px mt-0.5 h-0.5 w-full bg-gray-200"
                                    aria-hidden="true"
                                >
                                    <div
                                        className={cn(
                                            "h-full bg-primary transition-all duration-500 ease-in-out",
                                            isCompleted ? "w-full" : "w-0"
                                        )}
                                    />
                                </div>
                            )}
                            <div className="group relative flex flex-col items-center">
                                <span className="flex h-9 items-center">
                                    <span
                                        className={cn(
                                            "relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors duration-300",
                                            isCompleted
                                                ? "border-primary bg-primary hover:bg-primary-700"
                                                : isCurrent
                                                    ? "border-primary bg-white"
                                                    : "border-gray-300 bg-white"
                                        )}
                                    >
                                        {isCompleted ? (
                                            <Check className="h-5 w-5 text-white" aria-hidden="true" />
                                        ) : (
                                            <span
                                                className={cn(
                                                    "h-2.5 w-2.5 rounded-full",
                                                    isCurrent ? "bg-primary" : "bg-transparent"
                                                )}
                                            />
                                        )}
                                    </span>
                                </span>
                                <span className="mt-0.5 flex min-w-0 flex-col">
                                    <span
                                        className={cn(
                                            "text-xs font-semibold uppercase tracking-wide",
                                            isCurrent ? "text-primary" : "text-gray-500"
                                        )}
                                    >
                                        {step}
                                    </span>
                                </span>
                            </div>
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
}
