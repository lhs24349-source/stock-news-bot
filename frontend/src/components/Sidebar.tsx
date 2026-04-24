import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  Tags, 
  Send, 
  Clock, 
  History,
  Activity
} from 'lucide-react';

const navItems = [
  { title: 'Dashboard', href: '/', icon: LayoutDashboard },
  { title: '키워드 관리', href: '/keywords', icon: Tags },
  { title: '알림 채널', href: '/channels', icon: Send },
  { title: '스케줄 설정', href: '/schedule', icon: Clock },
  { title: '알림 내역', href: '/history', icon: History },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <div className="w-64 border-r bg-card/50 backdrop-blur-xl hidden md:flex flex-col h-screen sticky top-0">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20">
          <Activity size={18} strokeWidth={2.5} />
        </div>
        <h1 className="font-bold text-lg tracking-tight">Stock News Bot</h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group relative overflow-hidden",
                isActive 
                  ? "bg-primary/10 text-primary font-medium" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full" />
              )}
              <item.icon size={18} className={cn(
                "transition-transform duration-200",
                isActive ? "text-primary" : "group-hover:scale-110"
              )} />
              {item.title}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 mt-auto">
        <div className="rounded-lg bg-primary/5 border border-primary/10 p-4">
          <h4 className="text-sm font-medium mb-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            System Status
          </h4>
          <p className="text-xs text-muted-foreground">All services are running smoothly.</p>
        </div>
      </div>
    </div>
  );
}
