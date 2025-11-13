'use client';

import React, { useRef, useEffect, useState } from 'react';
import { gsap } from 'gsap';

export interface SplitTextProps {
  text: string;
  className?: string;
  delay?: number;
  duration?: number;
  ease?: string;
  splitType?: 'chars' | 'words' | 'lines';
  from?: gsap.TweenVars;
  to?: gsap.TweenVars;
  tag?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'span';
  textAlign?: React.CSSProperties['textAlign'];
  onLetterAnimationComplete?: () => void;
}

const SplitText: React.FC<SplitTextProps> = ({
  text,
  className = '',
  delay = 100,
  duration = 0.6,
  ease = 'power3.out',
  splitType = 'chars',
  from = { opacity: 0, y: 40 },
  to = { opacity: 1, y: 0 },
  tag = 'p',
  textAlign = 'center',
  onLetterAnimationComplete
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const checkFonts = async () => {
      if (typeof window !== 'undefined' && document.fonts) {
        if (document.fonts.status === 'loaded') {
          setIsReady(true);
        } else {
          await document.fonts.ready;
          setIsReady(true);
        }
      } else {
        setIsReady(true);
      }
    };
    checkFonts();
  }, []);

  useEffect(() => {
    if (!containerRef.current || !isReady || !text) return;

    const chars = Array.from(containerRef.current.children) as HTMLElement[];
    if (chars.length === 0) return;

    // Set initial state
    gsap.set(chars, from);

    // Animate
    gsap.to(chars, {
      ...to,
      duration,
      ease,
      stagger: delay / 1000,
      onComplete: () => {
        if (onLetterAnimationComplete) {
          onLetterAnimationComplete();
        }
      }
    });
  }, [isReady, text, delay, duration, ease, from, to, onLetterAnimationComplete]);

  const splitText = () => {
    if (!text) return null;
    
    if (splitType === 'chars') {
      const chars = text.split('').map((char, i) => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            whiteSpace: char === ' ' ? 'pre' : 'normal',
            transformStyle: 'preserve-3d',
            backfaceVisibility: 'hidden'
          }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ));
      return chars;
    } else if (splitType === 'words') {
      return text.split(' ').map((word, i) => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            marginRight: '0.25em'
          }}
        >
          {word}
        </span>
      ));
    }
    return text;
  };

  const style: React.CSSProperties = {
    textAlign,
    wordWrap: 'break-word',
  };

  const content = (
    <div 
      ref={containerRef} 
      style={{
        ...style,
        perspective: '1000px',
        perspectiveOrigin: '50% 50%'
      }} 
      className={className}
    >
      {isReady ? splitText() : null}
    </div>
  );

  switch (tag) {
    case 'h1':
      return <h1 className="inline-block w-full">{content}</h1>;
    case 'h2':
      return <h2 className="inline-block w-full">{content}</h2>;
    case 'h3':
      return <h3 className="inline-block w-full">{content}</h3>;
    case 'h4':
      return <h4 className="inline-block w-full">{content}</h4>;
    case 'h5':
      return <h5 className="inline-block w-full">{content}</h5>;
    case 'h6':
      return <h6 className="inline-block w-full">{content}</h6>;
    default:
      return content;
  }
};

export default SplitText;
