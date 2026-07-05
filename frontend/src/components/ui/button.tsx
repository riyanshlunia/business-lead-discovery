import { cn } from '@/lib/cn';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
};

export function Button({ className, variant = 'primary', ...props }: ButtonProps) {
  const styles = {
    primary: 'bg-teal-500 text-white hover:bg-teal-400 shadow-glow',
    secondary: 'bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-700',
    ghost: 'bg-transparent text-slate-200 hover:bg-slate-800',
  }[variant];

  return <button className={cn('inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition', styles, className)} {...props} />;
}
