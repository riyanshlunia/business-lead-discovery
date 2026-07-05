import { cn } from '@/lib/cn';

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn('w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-teal-400', props.className)} {...props} />;
}
