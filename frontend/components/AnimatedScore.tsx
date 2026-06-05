'use client';
import { useEffect, useRef, useState } from 'react';

interface Props {
  target: number;
  duration?: number;
  decimals?: number;
  suffix?: string;
  style?: React.CSSProperties;
}

export default function AnimatedScore({
  target,
  duration = 1400,
  decimals = 1,
  suffix = '',
  style,
}: Props) {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    const start = () => {
      startRef.current = performance.now();
      const step = (now: number) => {
        const elapsed = now - (startRef.current ?? now);
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        setValue(parseFloat((eased * target).toFixed(decimals)));
        if (progress < 1) {
          rafRef.current = requestAnimationFrame(step);
        } else {
          setValue(target);
        }
      };
      rafRef.current = requestAnimationFrame(step);
    };

    // Observe when element enters viewport
    const el = document.createElement('div');
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { start(); observer.disconnect(); } },
      { threshold: 0.3 }
    );
    // Attach to a hidden sentinel; simpler: just start after 200ms
    const t = setTimeout(start, 200);
    return () => {
      clearTimeout(t);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration, decimals]);

  return (
    <span style={style}>
      {value.toFixed(decimals)}{suffix}
    </span>
  );
}
