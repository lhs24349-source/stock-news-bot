import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import {
  Activity, Server, Radio, Database,
  Tags, Clock, Newspaper, TrendingUp,
  CheckCircle2, XCircle, AlertTriangle
} from 'lucide-react';

/** 스케줄 타입 → 한글 라벨 변환 */
function scheduleTypeLabel(type: string) {
  const map: Record<string, string> = {
    interval: '주기적 실행',
    interval_silent: '주기적 수집 (알림X)',
    digest: '지정 시간 요약',
    window_digest: '시간대 집중 수집/요약',
    backfill: '과거 데이터 수집',
  };
  return map[type] || type;
}

export function Dashboard() {
  // 헬스체크 (10초마다 갱신)
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await api.get('/health');
      return data;
    },
    refetchInterval: 10000,
  });

  // 대시보드 요약 데이터 (30초마다 갱신)
  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard');
      return data;
    },
    refetchInterval: 30000,
  });

  const isLoading = healthLoading || dashLoading;

  return (
    <div className="space-y-8">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-2">시스템 현황, 키워드 그룹, 스케줄 설정을 한눈에 확인하세요.</p>
      </div>

      {/* ── 상단 통계 카드 4개 ── */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* 시스템 상태 */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between pb-2">
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

        {/* 키워드 그룹 수 */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-medium">키워드 그룹</h3>
            <Tags className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-4 text-2xl font-bold">
            {isLoading ? '...' : dashboard?.keyword_groups_count ?? 0}
          </div>
        </div>

        {/* 등록된 스케줄 수 */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-medium">등록된 스케줄</h3>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-4 text-2xl font-bold">
            {isLoading ? '...' : dashboard?.schedules_count ?? 0}
          </div>
        </div>

        {/* 오늘 수집된 뉴스 */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="flex items-center justify-between pb-2">
            <h3 className="tracking-tight text-sm font-medium">오늘 수집 뉴스</h3>
            <Newspaper className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex items-baseline space-x-2 mt-4">
            <div className="text-2xl font-bold">
              {isLoading ? '...' : dashboard?.news_stats?.today ?? 0}
            </div>
            <span className="text-xs text-muted-foreground">
              / 전체 {dashboard?.news_stats?.total ?? 0}건
            </span>
          </div>
        </div>
      </div>

      {/* ── 키워드 그룹 / 알림 채널 요약 섹션 ── */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* 키워드 그룹 요약 카드 */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
          <div className="p-5 border-b bg-muted/20 flex items-center gap-2">
            <Tags className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-lg">활성 키워드 그룹</h3>
          </div>
          <div className="p-5">
            {isLoading ? (
              <div className="text-muted-foreground text-center py-6">로딩 중...</div>
            ) : !dashboard?.keyword_groups?.length ? (
              <div className="text-muted-foreground text-center py-6">
                <Tags className="mx-auto h-8 w-8 mb-2 opacity-40" />
                <p className="text-sm">등록된 키워드 그룹이 없습니다.</p>
                <p className="text-xs mt-1">키워드 관리 페이지에서 추가하세요.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {dashboard.keyword_groups.map((kg: any) => (
                  <div key={kg.id} className="border rounded-lg p-4 hover:bg-muted/30 transition-colors">
                    <h4 className="font-semibold text-sm mb-2">{kg.name}</h4>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {kg.keywords.map((kw: string) => (
                        <span key={kw} className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs font-medium">
                          {kw}
                        </span>
                      ))}
                    </div>
                    {kg.exclude_keywords?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {kg.exclude_keywords.map((kw: string) => (
                          <span key={kw} className="bg-destructive/10 text-destructive px-2 py-0.5 rounded text-xs font-medium">
                            ✕ {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 알림 채널 + 시스템 상태 요약 */}
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
          <div className="p-5 border-b bg-muted/20 flex items-center gap-2">
            <Radio className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-lg">시스템 상태</h3>
          </div>
          <div className="p-5 space-y-4">
            {/* DB / Redis 상태 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="border rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Database className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Database</span>
                </div>
                <div className="flex items-center gap-1.5">
                  {health?.db === 'ok' ? (
                    <><CheckCircle2 size={14} className="text-green-500" /><span className="text-sm text-green-600 font-medium">정상</span></>
                  ) : (
                    <><XCircle size={14} className="text-red-500" /><span className="text-sm text-red-600 font-medium">오류</span></>
                  )}
                </div>
              </div>
              <div className="border rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Server className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Redis</span>
                </div>
                <div className="flex items-center gap-1.5">
                  {health?.redis === 'ok' ? (
                    <><CheckCircle2 size={14} className="text-green-500" /><span className="text-sm text-green-600 font-medium">정상</span></>
                  ) : health?.redis === 'not_configured' ? (
                    <><AlertTriangle size={14} className="text-yellow-500" /><span className="text-sm text-yellow-600 font-medium">미설정</span></>
                  ) : (
                    <><XCircle size={14} className="text-red-500" /><span className="text-sm text-red-600 font-medium">오류</span></>
                  )}
                </div>
              </div>
            </div>

            {/* 알림 채널 */}
            <div className="border rounded-lg p-3">
              <h4 className="text-sm font-medium mb-2">알림 채널</h4>
              {!dashboard?.channels_configured?.length ? (
                <p className="text-xs text-muted-foreground">연동된 알림 채널이 없습니다. 채널 관리 페이지에서 추가하세요.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {dashboard.channels_configured.map((ch: string) => (
                    <span key={ch} className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2.5 py-1 rounded-md text-xs font-semibold">
                      ✓ {ch}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* 뉴스 통계 */}
            <div className="border rounded-lg p-3">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4" />
                뉴스 수집 현황
              </h4>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-lg font-bold text-primary">{dashboard?.news_stats?.recent_24h ?? 0}</div>
                  <div className="text-xs text-muted-foreground">최근 24시간</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{dashboard?.news_stats?.today ?? 0}</div>
                  <div className="text-xs text-muted-foreground">오늘</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{dashboard?.news_stats?.total ?? 0}</div>
                  <div className="text-xs text-muted-foreground">전체</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 스케줄 설정 요약 섹션 ── */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
        <div className="p-5 border-b bg-muted/20 flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-lg">등록된 스케줄</h3>
        </div>
        <div className="p-5">
          {isLoading ? (
            <div className="text-muted-foreground text-center py-6">로딩 중...</div>
          ) : !dashboard?.schedules?.length ? (
            <div className="text-muted-foreground text-center py-6">
              <Clock className="mx-auto h-8 w-8 mb-2 opacity-40" />
              <p className="text-sm">등록된 스케줄이 없습니다.</p>
              <p className="text-xs mt-1">스케줄 설정 페이지에서 추가하세요.</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {dashboard.schedules.map((sc: any) => (
                <div key={sc.id} className="border rounded-lg p-4 relative overflow-hidden hover:bg-muted/30 transition-colors">
                  <div className={`absolute left-0 top-0 bottom-0 w-1 ${sc.is_active ? 'bg-green-500' : 'bg-muted'}`} />
                  <div className="pl-3">
                    <h4 className="font-semibold text-sm">{sc.name}</h4>
                    <span className="text-xs text-primary font-medium uppercase tracking-wider">
                      {scheduleTypeLabel(sc.schedule_type)}
                    </span>
                    <div className="bg-muted/40 rounded p-2 mt-2 text-xs font-mono text-muted-foreground overflow-x-auto">
                      {JSON.stringify(sc.config, null, 1)}
                    </div>
                    {sc.last_run_at && (
                      <p className="text-xs text-muted-foreground mt-2">
                        마지막 실행: {new Date(sc.last_run_at).toLocaleString('ko-KR')}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
