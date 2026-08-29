'use client';

import * as React from 'react';
import { Sun, Moon } from 'lucide-react';
import { Button } from './button';

export function ThemeToggle({ className }: { className?: string }) {
  const [isDark, setIsDark] = React.useState(true);

  React.useEffect(() => {
    const frameId = requestAnimationFrame(() => {
      setIsDark(document.documentElement.classList.contains('dark'));
    });
    return () => cancelAnimationFrame(frameId);
  }, []);

  const toggleTheme = () => {
    const newMode = !isDark;
    setIsDark(newMode);
    if (newMode) {
      document.documentElement.classList.add('dark');
      try {
        localStorage.setItem('theme', 'dark');
      } catch {
        // ignore
      }
    } else {
      document.documentElement.classList.remove('dark');
      try {
        localStorage.setItem('theme', 'light');
      } catch {
        // ignore
      }
    }
  };

  return (
    <Button
      variant="outline"
      size="icon-sm"
      onClick={toggleTheme}
      className={className}
      title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
      aria-label="Toggle visual theme"
    >
      {isDark ? (
        <Sun className="h-3.5 w-3.5 text-amber-400" />
      ) : (
        <Moon className="h-3.5 w-3.5 text-slate-700" />
      )}
    </Button>
  );
}
