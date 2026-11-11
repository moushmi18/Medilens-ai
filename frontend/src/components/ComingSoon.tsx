import { Clock, ArrowRight } from 'lucide-react';
import { Card, Button } from './ui';
import { Link } from 'react-router-dom';
import type { ReactNode } from 'react';

interface ComingSoonProps {
  title: string;
  description: string;
  phase: number;
  icon: ReactNode;
  features?: string[];
}

export default function ComingSoon({
  title,
  description,
  phase,
  icon,
  features = [],
}: ComingSoonProps) {
  return (
    <div className="max-w-2xl mx-auto">
      <Card className="text-center">
        {/* Icon */}
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[#0d9488]/10 to-[#22c55e]/10 flex items-center justify-center text-[#0d9488]">
          {icon}
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-slate-900 mb-2">{title}</h1>

        {/* Description */}
        <p className="text-slate-600 mb-6 max-w-md mx-auto">{description}</p>

        {/* Phase badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#1e3a5f]/5 text-[#1e3a5f] mb-8">
          <Clock size={16} />
          <span className="text-sm font-medium">Coming in Phase {phase}</span>
        </div>

        {/* Feature preview */}
        {features.length > 0 && (
          <div className="border-t border-slate-200 pt-6 mt-2">
            <h3 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wide">
              Planned Features
            </h3>
            <ul className="text-left space-y-3 max-w-sm mx-auto">
              {features.map((feature, index) => (
                <li key={index} className="flex items-start gap-3 text-slate-600">
                  <div className="w-5 h-5 rounded-full bg-[#22c55e]/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <div className="w-2 h-2 rounded-full bg-[#22c55e]" />
                  </div>
                  <span className="text-sm">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Back to dashboard */}
        <div className="mt-8">
          <Link to="/">
            <Button variant="outline">
              Back to Dashboard
              <ArrowRight size={16} />
            </Button>
          </Link>
        </div>
      </Card>

      {/* Educational disclaimer */}
      <p className="text-center text-xs text-slate-400 mt-6">
        MediLens AI is for educational purposes only and does not provide medical advice.
      </p>
    </div>
  );
}
