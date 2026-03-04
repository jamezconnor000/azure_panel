/**
 * Norse Stat Card - Animated statistics display
 * "The runes speak of great numbers"
 */

import { useEffect, useState, useRef } from 'react';

interface NorseStatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color?: 'frost' | 'gold' | 'blood' | 'ember';
  rune?: string;
  animate?: boolean;
}

// Animated number counter
function AnimatedNumber({ value, duration = 1000 }: { value: number; duration?: number }) {
  const [displayValue, setDisplayValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const animationFrame = useRef<number | null>(null);

  useEffect(() => {
    if (typeof value !== 'number') return;

    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);

      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setDisplayValue(Math.floor(easeOutQuart * value));

      if (progress < 1) {
        animationFrame.current = requestAnimationFrame(animate);
      }
    };

    startTime.current = null;
    animationFrame.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current);
      }
    };
  }, [value, duration]);

  return <span>{displayValue.toLocaleString()}</span>;
}

export function NorseStatCard({
  title,
  value,
  icon,
  color = 'frost',
  rune = '᛭',
  animate = true,
}: NorseStatCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const colorStyles = {
    frost: {
      border: 'border-frost-blue/40',
      glow: 'hover:shadow-[0_0_30px_rgba(79,195,247,0.3)]',
      iconBg: 'bg-frost-blue/15',
      iconColor: 'text-frost-blue',
      accent: 'from-frost-blue/20 via-frost-glow/10 to-transparent',
      runeColor: 'text-frost-blue/50',
      valueColor: 'text-frost-light',
    },
    gold: {
      border: 'border-gold-primary/40',
      glow: 'hover:shadow-[0_0_30px_rgba(255,213,79,0.3)]',
      iconBg: 'bg-gold-primary/15',
      iconColor: 'text-gold-primary',
      accent: 'from-gold-primary/20 via-gold-glow/10 to-transparent',
      runeColor: 'text-gold-primary/50',
      valueColor: 'text-gold-light',
    },
    blood: {
      border: 'border-blood-red/40',
      glow: 'hover:shadow-[0_0_30px_rgba(239,68,68,0.3)]',
      iconBg: 'bg-blood-red/15',
      iconColor: 'text-blood-red',
      accent: 'from-blood-red/20 via-blood-dark/10 to-transparent',
      runeColor: 'text-blood-red/50',
      valueColor: 'text-blood-red',
    },
    ember: {
      border: 'border-ember-orange/40',
      glow: 'hover:shadow-[0_0_30px_rgba(255,112,67,0.3)]',
      iconBg: 'bg-ember-orange/15',
      iconColor: 'text-ember-orange',
      accent: 'from-ember-orange/20 via-ember-orange/10 to-transparent',
      runeColor: 'text-ember-orange/50',
      valueColor: 'text-ember-orange',
    },
  };

  const styles = colorStyles[color];
  const numericValue = typeof value === 'number' ? value : parseInt(value.toString()) || 0;

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl
        bg-gradient-to-br from-stone-dark/95 to-stone-darker
        border ${styles.border}
        transition-all duration-500 ease-out
        ${styles.glow}
        ${isHovered ? 'transform -translate-y-1' : ''}
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Top accent line */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${styles.accent}`} />

      {/* Corner rune */}
      <span className={`absolute top-3 right-4 text-lg ${styles.runeColor} transition-all duration-300 ${isHovered ? 'opacity-100 scale-110' : 'opacity-50'}`}>
        {rune}
      </span>

      {/* Content */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-3">
            {/* Title */}
            <p className="text-ice-white/60 text-sm font-rajdhani tracking-wider uppercase">
              {title}
            </p>

            {/* Value */}
            <p className={`text-4xl font-cinzel font-bold ${styles.valueColor} tracking-wide`}>
              {animate && typeof value === 'number' ? (
                <AnimatedNumber value={numericValue} />
              ) : (
                typeof value === 'number' ? value.toLocaleString() : value
              )}
            </p>
          </div>

          {/* Icon container */}
          <div className={`
            relative w-14 h-14 rounded-lg ${styles.iconBg} ${styles.iconColor}
            flex items-center justify-center
            transition-all duration-300
            ${isHovered ? 'scale-110' : ''}
          `}>
            {/* Pulse ring on hover */}
            {isHovered && (
              <div className={`absolute inset-0 rounded-lg ${styles.iconBg} animate-ping opacity-50`} />
            )}
            <span className="relative z-10">{icon}</span>
          </div>
        </div>
      </div>

      {/* Bottom shimmer on hover */}
      <div
        className={`
          absolute bottom-0 left-0 right-0 h-16
          bg-gradient-to-t ${styles.accent}
          transition-opacity duration-500
          ${isHovered ? 'opacity-100' : 'opacity-0'}
        `}
      />

      {/* Hover shimmer effect */}
      <div
        className={`
          absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent
          transition-transform duration-700
          ${isHovered ? 'translate-x-full' : '-translate-x-full'}
        `}
      />
    </div>
  );
}

export default NorseStatCard;
