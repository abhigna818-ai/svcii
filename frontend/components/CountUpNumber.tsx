'use client';
import { useCountUp } from '@/hooks/useCountUp';

interface Props {
  target: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  style?: React.CSSProperties;
  className?: string;
}

export default function CountUpNumber({ target, decimals = 0, suffix = '', prefix = '', style, className }: Props) {
  const { ref, display } = useCountUp(target, { decimals });
  return (
    <span ref={ref as React.RefObject<HTMLSpanElement>} className={className} style={style}>
      {prefix}{display}{suffix}
    </span>
  );
}
