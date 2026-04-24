import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Activity, Server, Radio, Database } from 'lucide-react';

export function Dashboard() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await api.get('/health');
      return data;
    },
    refetchInterval: 10000, // 10초마다 상태 갱신
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-2">시스템 현황과 백엔드 헬스체크 결과를 한눈에 확인하세요.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Status Card */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">System Status</h3>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex items-baseline space-x-3 mt-4">
            <div className="text-2xl font-bold capitalize">
              {isLoading ? '...' : health?.status || 'Unknown'}
            </div>
            {health?.status === 'ok' && (
              <span className="flex h-3 w-3 rounded-full bg-green-500 animate-pulse" />
            )}
          </div>
        </div>

        {/* DB Card */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Database</h3>
            <Database className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-4 text-2xl font-bold capitalize">
            {isLoading ? '...' : health?.db || 'Unknown'}
          </div>
        </div>

        {/* Redis Card */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
           <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Cache (Redis)</h3>
            <Server className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-4 text-2xl font-bold capitalize">
            {isLoading ? '...' : health?.redis || 'Disabled'}
          </div>
        </div>

        {/* Channels Card */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
           <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Active Channels</h3>
            <Radio className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-4 text-2xl font-bold">
            {isLoading ? '...' : health?.channels?.length || 0}
          </div>
        </div>
      </div>

      <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
        <div className="p-6 border-b bg-muted/20">
          <h3 className="font-semibold text-lg">System Detail</h3>
        </div>
        <div className="p-6">
          <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto text-muted-foreground font-mono">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
