/**
 * Runic Icons - Norse-styled SVG icons
 * Icons that look runic but represent their function
 */

import React from 'react';

interface RunicIconProps {
  size?: number;
  className?: string;
  color?: string;
}

// Runic Door - ᚨ inspired, looks like a doorway
export function RunicDoor({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Main doorframe */}
      <path
        d="M5 4 L5 20 L19 20 L19 4 L5 4"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Inner archway */}
      <path
        d="M8 20 L8 9 Q12 6 16 9 L16 20"
        stroke={color}
        strokeWidth="1.5"
        fill="none"
      />
      {/* Runic marks */}
      <line x1="12" y1="4" x2="12" y2="7" stroke={color} strokeWidth="1.5" />
      <circle cx="14" cy="14" r="1" fill={color} />
    </svg>
  );
}

// Runic Person - ᛗ (Mannaz) inspired, human figure
export function RunicPerson({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Head */}
      <circle cx="12" cy="6" r="3" stroke={color} strokeWidth="2" fill="none" />
      {/* Body - runic style */}
      <path
        d="M12 9 L12 21 M6 13 L12 17 L18 13 M8 21 L12 17 L16 21"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
    </svg>
  );
}

// Runic Shield - ᛉ (Algiz) inspired, protection
export function RunicShield({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Shield outline */}
      <path
        d="M12 2 L4 6 L4 12 Q4 18 12 22 Q20 18 20 12 L20 6 L12 2 Z"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Algiz rune inside */}
      <path
        d="M12 7 L12 17 M8 11 L12 7 L16 11"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="square"
      />
    </svg>
  );
}

// Runic Activity/Events - ᚱ (Raido) inspired, journey/movement
export function RunicActivity({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Raido-inspired path */}
      <path
        d="M4 12 L8 4 L12 12 L16 4 L20 12"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      <path
        d="M4 20 L8 12 L12 20 L16 12 L20 20"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
    </svg>
  );
}

// Runic Settings/Knowledge - ᚲ (Kenaz) inspired, torch/knowledge
export function RunicSettings({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Gear-like rune pattern */}
      <circle cx="12" cy="12" r="3" stroke={color} strokeWidth="2" fill="none" />
      {/* Runic spokes */}
      <path
        d="M12 2 L12 6 M12 18 L12 22
           M2 12 L6 12 M18 12 L22 12
           M5 5 L8 8 M16 16 L19 19
           M19 5 L16 8 M8 16 L5 19"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
      />
    </svg>
  );
}

// Runic Key/Access - ᚦ (Thurisaz) inspired, gateway
export function RunicKey({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Key head - angular runic style */}
      <path
        d="M6 4 L10 4 L14 8 L14 12 L10 16 L6 16 L6 4 Z"
        stroke={color}
        strokeWidth="2"
        fill="none"
      />
      {/* Key shaft */}
      <path
        d="M14 12 L20 12 M17 12 L17 15 M20 12 L20 15"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
      />
      {/* Central dot */}
      <circle cx="10" cy="10" r="1.5" fill={color} />
    </svg>
  );
}

// Runic Lock
export function RunicLock({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Lock body - angular */}
      <path
        d="M6 10 L6 20 L18 20 L18 10 L6 10"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Shackle - angular */}
      <path
        d="M8 10 L8 7 Q8 4 12 4 Q16 4 16 7 L16 10"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Keyhole - runic diamond */}
      <path
        d="M12 13 L14 15 L12 17 L10 15 Z"
        stroke={color}
        strokeWidth="1.5"
        fill={color}
      />
    </svg>
  );
}

// Runic Unlock
export function RunicUnlock({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Lock body - angular */}
      <path
        d="M6 10 L6 20 L18 20 L18 10 L6 10"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Shackle - open */}
      <path
        d="M8 10 L8 7 Q8 4 12 4 Q16 4 16 7"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Keyhole - runic diamond */}
      <path
        d="M12 13 L14 15 L12 17 L10 15 Z"
        stroke={color}
        strokeWidth="1.5"
        fill={color}
      />
    </svg>
  );
}

// Runic Alert/Warning - inspired by ᚺ (Hagalaz)
export function RunicAlert({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Triangle */}
      <path
        d="M12 3 L22 20 L2 20 Z"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Exclamation - runic style */}
      <path
        d="M12 9 L12 14"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
      />
      <circle cx="12" cy="17" r="1" fill={color} />
    </svg>
  );
}

// Runic Success/Check - inspired by ᚹ (Wunjo)
export function RunicSuccess({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Circle */}
      <circle cx="12" cy="12" r="9" stroke={color} strokeWidth="2" fill="none" />
      {/* Angular checkmark */}
      <path
        d="M8 12 L11 15 L16 9"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
    </svg>
  );
}

// Runic Search - Eye inspired, ᛖ (Ehwaz) movement
export function RunicSearch({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Magnifying glass circle - angular */}
      <path
        d="M10 4 L16 4 L18 10 L16 16 L10 16 L4 10 L10 4"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
        transform="rotate(-10 11 10)"
      />
      {/* Handle */}
      <path
        d="M15 15 L20 20"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
      />
      {/* Inner dot */}
      <circle cx="11" cy="10" r="2" stroke={color} strokeWidth="1.5" fill="none" />
    </svg>
  );
}

// Runic Plus/Add - Gebo inspired cross
export function RunicPlus({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <path
        d="M12 4 L12 20 M4 12 L20 12"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      {/* Corner accents */}
      <path
        d="M6 6 L8 8 M18 6 L16 8 M6 18 L8 16 M18 18 L16 16"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="square"
        opacity="0.5"
      />
    </svg>
  );
}

// Runic Close/X
export function RunicClose({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <path
        d="M6 6 L18 18 M18 6 L6 18"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="square"
      />
    </svg>
  );
}

// Runic Refresh - Jera cycle inspired
export function RunicRefresh({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Circular arrows - angular style */}
      <path
        d="M4 12 Q4 6 12 6 Q18 6 19 10"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      <path
        d="M20 12 Q20 18 12 18 Q6 18 5 14"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Arrow heads - angular */}
      <path d="M17 6 L19 10 L23 8" stroke={color} strokeWidth="2" strokeLinecap="square" fill="none" />
      <path d="M7 18 L5 14 L1 16" stroke={color} strokeWidth="2" strokeLinecap="square" fill="none" />
    </svg>
  );
}

// Runic Bell/Notification
export function RunicBell({ size = 24, className = '', color = 'currentColor' }: RunicIconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      {/* Bell shape - angular */}
      <path
        d="M12 3 L12 5 M8 5 L8 12 L4 16 L20 16 L16 12 L16 5 L8 5"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="square"
        fill="none"
      />
      {/* Clapper */}
      <path d="M10 19 Q12 21 14 19" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

// Export mapping for easy use
export const RunicIcons = {
  door: RunicDoor,
  person: RunicPerson,
  shield: RunicShield,
  activity: RunicActivity,
  settings: RunicSettings,
  key: RunicKey,
  lock: RunicLock,
  unlock: RunicUnlock,
  alert: RunicAlert,
  success: RunicSuccess,
  search: RunicSearch,
  plus: RunicPlus,
  close: RunicClose,
  refresh: RunicRefresh,
  bell: RunicBell,
};
