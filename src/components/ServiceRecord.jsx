
import { Medal, Coins, Flame, Skull, Crosshair } from 'lucide-react';

const ServiceRecord = ({ medals }) => {
    if (!medals || Object.keys(medals).length === 0) return null;

    const medalIcons = {
        'MVP': { icon: CrownIcon, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
        'Immortal Slayer': { icon: Crosshair, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        'Cannoneer': { icon: Skull, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
        'Coins': { icon: Coins, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
        'Gems': { icon: Medal, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
        'Guardian': { icon: ShieldIcon, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' }
    };

    // Helper components to avoid imports for now if simple
    function CrownIcon({ className }) { return <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m2 4 3 12h14l3-12-6 7-4-3-4 3-6-7zm5 16h10v2H7z" /></svg> }
    function ShieldIcon({ className }) { return <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg> }

    return (
        <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-6">
                <Medal className="w-5 h-5 text-amber-400" />
                <h3 className="text-sm font-bold text-amber-400 uppercase tracking-widest">Commendations & Service Ribbons</h3>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(medals).map(([name, count], i) => {
                    // Match partial keys
                    let style = { icon: Medal, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20' };
                    if (name.includes('MVP')) style = medalIcons['MVP'];
                    else if (name.includes('Immortal')) style = medalIcons['Immortal Slayer'];
                    else if (name.includes('Cannoneer') || name.includes('Curse')) style = medalIcons['Cannoneer'];
                    else if (name.includes('Coins') || name.includes('Bosun')) style = medalIcons['Coins'];
                    else if (name.includes('Gems') || name.includes('Consort')) style = medalIcons['Gems'];
                    else if (name.includes('Guardian') || name.includes('Altar') || name.includes('Temple')) style = medalIcons['Guardian'];

                    const Icon = style.icon;

                    return (
                        <div key={i} className={`flex items-center gap-3 p-3 rounded-lg border ${style.bg} ${style.color}`}>
                            <Icon className="w-5 h-5 opacity-80" />
                            <div>
                                <div className="text-xl font-black leading-none">{count}</div>
                                <div className="text-[10px] uppercase font-bold opacity-70 leading-tight mt-1">{name}</div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ServiceRecord;
