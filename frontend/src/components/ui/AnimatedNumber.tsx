import { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

interface AnimatedNumberProps {
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
  duration?: number;
}

export function AnimatedNumber({
  value,
  prefix = '',
  suffix = '',
  decimals = 2,
  className = '',
  duration = 0.5,
}: AnimatedNumberProps) {
  const spring = useSpring(0, { duration: duration * 1000, bounce: 0 });
  const display = useTransform(spring, (current) =>
    `${prefix}${current.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}${suffix}`
  );

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return (
    <motion.span className={`metric-value ${className}`}>
      {display}
    </motion.span>
  );
}

interface AnimatedCurrencyProps {
  value: number;
  showSign?: boolean;
  className?: string;
}

export function AnimatedCurrency({
  value,
  showSign = false,
  className = '',
}: AnimatedCurrencyProps) {
  const [displayValue, setDisplayValue] = useState(value);
  const prevValue = useRef(value);
  const isPositive = value >= 0;

  useEffect(() => {
    const startValue = prevValue.current;
    const endValue = value;
    const duration = 500;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function
      const eased = 1 - Math.pow(1 - progress, 3);
      
      const current = startValue + (endValue - startValue) * eased;
      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
    prevValue.current = value;
  }, [value]);

  const formattedValue = Math.abs(displayValue).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <motion.span
      className={`metric-value ${className}`}
      initial={{ scale: 1 }}
      animate={{ scale: [1, 1.02, 1] }}
      transition={{ duration: 0.2 }}
      key={Math.round(value)}
    >
      {showSign && (isPositive ? '+' : '')}
      ${isPositive ? '' : '-'}{formattedValue}
    </motion.span>
  );
}

interface AnimatedPercentProps {
  value: number;
  showSign?: boolean;
  className?: string;
}

export function AnimatedPercent({
  value,
  showSign = true,
  className = '',
}: AnimatedPercentProps) {
  const [displayValue, setDisplayValue] = useState(value);
  const prevValue = useRef(value);
  const isPositive = value >= 0;

  useEffect(() => {
    const startValue = prevValue.current;
    const endValue = value;
    const duration = 500;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = startValue + (endValue - startValue) * eased;
      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
    prevValue.current = value;
  }, [value]);

  return (
    <motion.span
      className={`metric-value ${className}`}
      initial={{ opacity: 0.8 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      {showSign && (isPositive ? '+' : '')}{displayValue.toFixed(2)}%
    </motion.span>
  );
}
