import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Clock, Plus, Trash2, Calendar, PlayCircle } from 'lucide-react';
import { format } from 'date-fns';

export function Schedule() {
  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedule'],
    queryFn: async () => {
      const { data } = await api.get('/schedule');
      return data;
    },
  });

  const getScheduleTypeLabel = (type: string) => {
    switch (type) {
      case 'interval': return '주기적 실행';
      case 'digest': return '지정 시간 요약 (Cron)';
      case 'backfill': return '과거 데이터 수집';
      case 'event': return '단발성 이벤트';
      default: return type;
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <Clock className="text-primary" />
            스케줄 설정
          </h1>
          <p className="text-muted-foreground mt-2">뉴스 수집 및 알림 전송 주기를 관리합니다.</p>
        </div>
        <button className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors">
          <Plus size={18} />
          새 스케줄 추가
        </button>
      </div>

      {isLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">로딩 중...</div>
      ) : schedules?.length === 0 ? (
        <div className="border-2 border-dashed border-muted rounded-xl p-12 text-center">
          <Calendar className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">등록된 스케줄이 없습니다</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6">원하는 시간에 뉴스를 수집하도록 스케줄을 생성하세요.</p>
          <button className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
            첫 스케줄 만들기
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {schedules?.map((schedule: any) => (
            <div key={schedule.id} className="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
              {/* 왼쪽 상태 표시줄 */}
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${schedule.is_active ? 'bg-green-500' : 'bg-muted'}`} />
              
              <div className="p-6 pl-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex flex-col">
                    <h3 className="font-semibold text-lg">{schedule.name}</h3>
                    <span className="text-xs font-medium text-primary uppercase tracking-wider">
                      {getScheduleTypeLabel(schedule.schedule_type)}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button className="p-2 text-muted-foreground hover:text-primary transition-colors bg-muted/50 rounded-md" title="지금 즉시 실행">
                      <PlayCircle size={18} />
                    </button>
                    <button className="p-2 text-muted-foreground hover:text-destructive transition-colors bg-muted/50 rounded-md">
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                <div className="bg-muted/30 rounded-lg p-3 mt-4 text-sm font-mono text-muted-foreground overflow-x-auto">
                  {JSON.stringify(schedule.config, null, 2)}
                </div>

                <div className="pt-4 mt-4 border-t grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground block text-xs mb-1">마지막 실행</span>
                    <span className="font-medium text-foreground">
                      {schedule.last_run_at ? format(new Date(schedule.last_run_at), 'yyyy-MM-dd HH:mm') : '없음'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs mb-1">다음 실행 예정</span>
                    <span className="font-medium text-primary">
                      {schedule.next_run_at ? format(new Date(schedule.next_run_at), 'yyyy-MM-dd HH:mm') : '대기 중'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
