'use client';

import React from 'react';

type Props = {
  value: 'budget' | 'premium';
  onChange: (v: 'budget' | 'premium') => void;
};

export default function SegmentedToggle({ value, onChange }: Props) {
  return (
    <div className="relative inline-flex items-center rounded-full bg-white/60 dark:bg-white/10 p-1 shadow-glass backdrop-blur-md">
      <div
        aria-hidden
        className={`absolute top-1 left-1 h-7 w-[calc(50%-0.5rem)] rounded-full transition-transform duration-200 ease-in-out ${
          value === 'premium' ? 'translate-x-full -translate-x-[0.125rem] bg-indigo-600' : 'translate-x-0 bg-indigo-500'
        }`}
        style={{ transform: value === 'premium' ? 'translateX(100%)' : 'translateX(0%)' }}
      />

      <button
        type="button"
        role="tab"
        aria-selected={value === 'budget'}
        onClick={() => onChange('budget')}
        className={`relative z-10 flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          value === 'budget' ? 'text-white' : 'text-slate-200 hover:bg-white/20 hover:text-white'
        }`}
      >
        Budget-Friendly
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={value === 'premium'}
        onClick={() => onChange('premium')}
        className={`relative z-10 flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          value === 'premium' ? 'text-white' : 'text-slate-200 hover:bg-white/20 hover:text-white'
        }`}
      >
        Premium Quality
      </button>
    </div>
  );
}
