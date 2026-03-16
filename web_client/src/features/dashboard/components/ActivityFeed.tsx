import React from 'react';
import { Clock, LucideIcon } from 'lucide-react';

interface ActivityItem {
    action: string;
    title: string;
    time: string;
    icon: LucideIcon;
    color: string;
}

interface ActivityFeedProps {
    activities: ActivityItem[];
    settings?: any;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities }) => {
    return (
        <div className="glass-panel p-8 rounded-premium-lg relative overflow-hidden group shadow-premium">
            <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] mb-6 flex items-center justify-between">
                Actividad Reciente
                <Clock className="w-3.5 h-3.5 opacity-40" />
            </h4>
            <div className="space-y-5">
                {activities.map((act, i) => (
                    <div key={i} className="flex items-center gap-4 group/item">
                        <div className={`p-2 rounded-premium-sm bg-[var(--panel-bg-subtle)] ${act.color} group-hover/item:scale-110 transition-transform`}>
                            <act.icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-white truncate">{act.title}</p>
                            <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-0.5">{act.action} • {act.time}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
