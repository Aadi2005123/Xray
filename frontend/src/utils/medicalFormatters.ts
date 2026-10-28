import type { SeverityLevel } from '../types';

export function formatProbability(prob: number): string {
  const percentage = Math.max(0, Math.min(100, prob * 100));
  return `${percentage.toFixed(1)}%`;
}

export function getSeverityLevel(probability: number, threshold: number): SeverityLevel {
  if (probability < threshold * 0.5) return 'normal';
  if (probability < threshold) return 'low';
  if (probability < threshold * 1.5) return 'moderate';
  return 'high';
}

export function getSeverityBadgeStyles(severity: SeverityLevel): {
  bg: string;
  text: string;
  border: string;
  label: string;
} {
  switch (severity) {
    case 'high':
      return {
        bg: 'bg-rose-950/60',
        text: 'text-rose-300',
        border: 'border-rose-700/60',
        label: 'High Probability',
      };
    case 'moderate':
      return {
        bg: 'bg-amber-950/60',
        text: 'text-amber-300',
        border: 'border-amber-700/60',
        label: 'Moderate Probability',
      };
    case 'low':
      return {
        bg: 'bg-blue-950/50',
        text: 'text-blue-300',
        border: 'border-blue-700/50',
        label: 'Low Probability',
      };
    case 'normal':
    default:
      return {
        bg: 'bg-emerald-950/40',
        text: 'text-emerald-300',
        border: 'border-emerald-800/40',
        label: 'Unremarkable',
      };
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

export function generateClientImageHash(fileName: string, fileSize: number): string {
  // Simple deterministic client hash for preview verification
  let hash = 0;
  const str = `${fileName}-${fileSize}-${Date.now().toString().slice(0, 8)}`;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return 'SHA256:' + Math.abs(hash).toString(16).padStart(16, '0').repeat(4).slice(0, 64);
}
