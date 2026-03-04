/**
 * Frost Particles - Norse Ice Effect
 * Floating ice crystals and snow particles
 */

import { useCallback } from 'react';
import Particles from '@tsparticles/react';
import { loadSlim } from '@tsparticles/slim';
import type { Engine } from '@tsparticles/engine';

export function FrostParticles() {
  const particlesInit = useCallback(async (engine: Engine) => {
    await loadSlim(engine);
  }, []);

  return (
    <Particles
      id="frost-particles"
      init={particlesInit}
      options={{
        fullScreen: {
          enable: true,
          zIndex: 0,
        },
        particles: {
          number: {
            value: 50,
            density: {
              enable: true,
            },
          },
          color: {
            value: ['#4FC3F7', '#81D4FA', '#E3F2FD', '#FFFFFF'],
          },
          shape: {
            type: ['circle', 'star'],
          },
          opacity: {
            value: { min: 0.1, max: 0.5 },
            animation: {
              enable: true,
              speed: 0.5,
              sync: false,
            },
          },
          size: {
            value: { min: 1, max: 4 },
            animation: {
              enable: true,
              speed: 2,
              sync: false,
            },
          },
          move: {
            enable: true,
            speed: { min: 0.5, max: 2 },
            direction: 'bottom',
            random: true,
            straight: false,
            outModes: {
              default: 'out',
            },
            drift: 2,
          },
          wobble: {
            enable: true,
            distance: 10,
            speed: 5,
          },
          twinkle: {
            particles: {
              enable: true,
              frequency: 0.05,
              opacity: 1,
              color: {
                value: '#00E5FF',
              },
            },
          },
        },
        interactivity: {
          events: {
            onHover: {
              enable: true,
              mode: 'repulse',
            },
          },
          modes: {
            repulse: {
              distance: 100,
              duration: 0.4,
            },
          },
        },
        detectRetina: true,
      }}
    />
  );
}

export default FrostParticles;
