import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface TextProps {
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'caption' | 'small';
  children: React.ReactNode;
  className?: string;
}

export const Text: React.FC<TextProps> = ({ variant = 'body', children, className }) => {
  const variants = {
    h1: 'text-4xl font-bold tracking-tight text-gaatha-gray-900',
    h2: 'text-2xl font-semibold text-gaatha-gray-900',
    h3: 'text-xl font-medium text-gaatha-gray-800',
    body: 'text-base text-gaatha-gray-800 leading-relaxed',
    caption: 'text-sm font-medium text-gaatha-gray-600',
    small: 'text-xs text-gaatha-gray-500',
  };

  const Tag = variant.startsWith('h') ? (variant as keyof JSX.IntrinsicElements) : 'p';

  return (
    <Tag className={cn(variants[variant], className)}>
      {children}
    </Tag>
  );
};