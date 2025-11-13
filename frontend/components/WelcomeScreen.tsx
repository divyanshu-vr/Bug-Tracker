'use client';

import React, { useEffect, useState, useRef } from 'react';
import { gsap } from 'gsap';
import SplitText from './SplitText';
import { useUser } from '@/contexts/UserContext';
import { useNavbar } from '@/contexts/NavbarContext';

interface WelcomeScreenProps {
  onComplete: () => void;
  isDataLoaded: boolean;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onComplete, isDataLoaded }) => {
  const { currentUser } = useUser();
  const { setNavbarVisible } = useNavbar();
  const [stage, setStage] = useState<'loading' | 'welcome' | 'complete'>('loading');
  const [dots, setDots] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const spinnerRef = useRef<HTMLDivElement>(null);
  const welcomeRef = useRef<HTMLDivElement>(null);

  // Hide navbar when component mounts
  useEffect(() => {
    setNavbarVisible(false);
    return () => {
      // Show navbar when component unmounts
      setNavbarVisible(true);
    };
  }, [setNavbarVisible]);

  // Animate dots for loading text
  useEffect(() => {
    if (stage !== 'loading') return;
    
    const interval = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500); // Change every 500ms

    return () => clearInterval(interval);
  }, [stage]);

  useEffect(() => {
    // Only transition to welcome stage when data is loaded
    if (isDataLoaded && stage === 'loading') {
      // Morph spinner into welcome text
      if (spinnerRef.current) {
        gsap.to(spinnerRef.current, {
          scale: 0,
          opacity: 0,
          duration: 0.5,
          ease: 'power2.in',
          onComplete: () => {
            setStage('welcome');
          }
        });
      }
    }
  }, [isDataLoaded, stage]);

  useEffect(() => {
    if (stage === 'welcome' && welcomeRef.current) {
      // Fade in welcome container
      gsap.fromTo(
        welcomeRef.current,
        { scale: 0.8, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.6, ease: 'back.out(1.7)' }
      );
    }
  }, [stage]);

  const handleWelcomeAnimationComplete = () => {
    // Wait a bit after welcome text completes, then slide up
    setTimeout(() => {
      if (containerRef.current) {
        // Slide up the entire welcome screen (background + text together)
        gsap.to(containerRef.current, {
          y: '-100%',
          duration: 0.8,
          ease: 'power2.inOut',
          onComplete: () => {
            setStage('complete');
            onComplete();
          }
        });
      }
    }, 1000);
  };

  if (stage === 'complete') {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-white dark:bg-gray-900"
      style={{ backgroundColor: 'white' }}
    >
      {stage === 'loading' && (
        <div ref={spinnerRef} className="flex flex-col items-center gap-6">
          {/* Cool Spinning Bug Icon */}
          <div className="relative w-24 h-24">
            {/* Outer spinning ring */}
            <div className="absolute inset-0 border-4 border-primary/20 rounded-full animate-spin-slow"></div>
            
            {/* Middle spinning ring */}
            <div className="absolute inset-2 border-4 border-primary/40 rounded-full animate-spin-reverse"></div>
            
            {/* Inner pulsing circle */}
            <div className="absolute inset-4 bg-primary/20 rounded-full animate-pulse"></div>
            
            {/* Bug Icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-10 h-10 text-primary animate-bounce-subtle"
              >
                <path d="m8 2 1.88 1.88" />
                <path d="M14.12 3.88 16 2" />
                <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" />
                <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6" />
                <path d="M12 20v-9" />
                <path d="M6.53 9C4.6 8.8 3 7.1 3 5" />
                <path d="M6 13H2" />
                <path d="M3 21c0-2.1 1.7-3.9 3.8-4" />
                <path d="M20.97 5c0 2.1-1.6 3.8-3.5 4" />
                <path d="M22 13h-4" />
                <path d="M17.2 17c2.1.1 3.8 1.9 3.8 4" />
              </svg>
            </div>
          </div>

          {/* Loading text with dots animation */}
          <div className="flex items-center">
            <span className="text-lg font-medium text-muted-foreground">
              Loading<span className="inline-block w-6 text-left">{dots}</span>
            </span>
          </div>
        </div>
      )}

      {stage === 'welcome' && (
        <div ref={welcomeRef} className="text-center px-4">
          <div className="text-5xl md:text-6xl lg:text-7xl font-bold text-primary">
            <SplitText
              text={`Welcome Back, ${currentUser?.name || 'Guest'}`}
              delay={50}
              duration={0.8}
              ease="power3.out"
              splitType="words"
              from={{ opacity: 0, y: 60, rotationX: -90 }}
              to={{ opacity: 1, y: 0, rotationX: 0 }}
              onLetterAnimationComplete={handleWelcomeAnimationComplete}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default WelcomeScreen;
