"use client";

import { useState, useEffect } from "react";
import type { JSX } from "react/jsx-runtime";

interface TimeLeft {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

const calculateTimeLeft = (targetDate: Date): TimeLeft => {
  const difference = +targetDate - +new Date();
  let timeLeft: TimeLeft = {
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  };

  if (difference > 0) {
    timeLeft = {
      days: Math.floor(difference / (1000 * 60 * 60 * 24)),
      hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
      minutes: Math.floor((difference / 1000 / 60) % 60),
      seconds: Math.floor((difference / 1000) % 60)
    };
  }

  return timeLeft;
};

export function Countdown() {
  // Initialize targetDate only once using useState's functional update
  const [targetDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() + 30); // Set to 30 days from the initial render time
    return date;
  });

  const [timeLeft, setTimeLeft] = useState<TimeLeft>(calculateTimeLeft(targetDate));

  useEffect(() => {
    // Use setInterval for continuous updates
    const timer = setInterval(() => {
      setTimeLeft(calculateTimeLeft(targetDate));
    }, 1000); // Update every second

    // Clean up the interval when the component unmounts or targetDate changes (though targetDate is stable here)
    return () => clearInterval(timer);
  }, [targetDate]); // Dependency array ensures effect runs only if targetDate changes (which it won't after initial render)

  const timerComponents: JSX.Element[] = [];

  Object.keys(timeLeft).forEach((interval) => {
    const value = timeLeft[interval as keyof TimeLeft];
    timerComponents.push(
      <div key={interval} className="flex flex-col items-center">
        <span className="text-5xl font-bold">{value < 10 ? `0${value}` : value}</span>
        <span className="text-sm uppercase opacity-80">{interval}</span>
      </div>
    );
  });

  return (
    <div className="flex justify-center gap-6 md:gap-8">
      {timerComponents.length ? timerComponents : <span>Time's up!</span>}
    </div>
  );
}
