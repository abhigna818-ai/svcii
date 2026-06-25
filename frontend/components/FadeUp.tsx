'use client';
import type { ReactNode } from 'react';
import { useScrollAnimation } from '@/hooks/useScrollAnimation';

interface Props {
  children: ReactNode;
  className?: string;
  stagger?: boolean;
  style?: React.CSSProperties;
}

export default function FadeUp({ children, className = '', stagger = false, style }: Props) {
  const { ref, visible } = useScrollAnimation<HTMLDivElement>();
  const classes = [stagger ? 'stagger-children' : 'fade-up', visible ? 'visible' : '', className]
    .filter(Boolean)
    .join(' ');
  return (
    <div ref={ref} className={classes} style={style}>
      {children}
    </div>
  );
}
