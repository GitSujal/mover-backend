"use client";

import { useState } from "react";
import { WizardStepper } from "@/components/booking/WizardStepper";
import { Step1MoveDetails } from "@/components/booking/Step1MoveDetails";
import { Step2Inventory } from "@/components/booking/Step2Inventory";
import { Step3Quote } from "@/components/booking/Step3Quote";
import { Step4Review } from "@/components/booking/Step4Review";

const STEPS = ["Move Details", "Inventory", "Get Quote", "Review & Book"];

export default function BookPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [bookingData, setBookingData] = useState({});

  const handleNext = (data: any) => {
    setBookingData((prev) => ({ ...prev, ...data }));
    setCurrentStep((prev) => Math.min(prev + 1, STEPS.length));
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <WizardStepper currentStep={currentStep} steps={STEPS} />
        </div>

        <div className="mt-8">
          {currentStep === 1 && (
            <Step1MoveDetails onNext={handleNext} defaultValues={bookingData} />
          )}
          {currentStep === 2 && (
            <Step2Inventory
              onNext={handleNext}
              onBack={handleBack}
              defaultValues={bookingData}
            />
          )}
          {currentStep === 3 && (
            <Step3Quote
              onNext={handleNext}
              onBack={handleBack}
              bookingData={bookingData}
            />
          )}
          {currentStep === 4 && (
            <Step4Review onBack={handleBack} bookingData={bookingData} />
          )}
        </div>
      </div>
    </div>
  );
}
