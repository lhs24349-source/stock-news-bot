import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Clock, Plus, Trash2, Calendar, PlayCircle, X } from 'lucide-react';
import { format } from 'date-fns';

export function Schedule() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', schedule_type: 'interval', interval_minutes: 60, cron: '0 16 * * *', start_hour: 3, end_hour: 7 });

  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedule'],
    queryFn: async () => {
      const { data } = await api.get('/schedule');
      return data;
    },
  });

  const addMutation = useMutation({
    mutationFn: async (newData: any) => {
      let config: any = {};
      if (newData.schedule_type === 'digest') config = { cron_expression: newData.cron };
      else if (newData.schedule_type === 'window_digest') config = { start_hour: newData.start_hour, end_hour: newData.end_hour, interval_minutes: newData.interval_minutes };
      else config = { minutes: Number(newData.interval_minutes) };

      await api.post('/schedule', {
        name: newData.name,
        schedule_type: newData.schedule_type,
        config: config,
        is_active: true
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      setIsModalOpen(false);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      if (confirm('스케줄을 삭제하시겠습니까?')) await api.delete(`/schedule/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedule'] })
  });

  const runMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/schedule/${id}/run`);
      alert('스케줄 수동 실행을 시작했습니다.');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addMutation.mutate(formData);
  };

  const getScheduleTypeLabel = (type: string) => {
    switch (type) {
      case 'interval': return '주기적 실행';
      case 'digest': return '지정 시간 요약';
      case 'backfill': return '과거 데이터 수집';
      default: return type;
    }
  };

  return (
    <div className="space-y-8 relative">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <Clock className="text-primary" />
            스케줄 설정
          </h1>
          <p className="text-muted-foreground mt-2">뉴스 수집 및 알림 전송 주기를 관리합니다.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors"
        >
          <Plus size={18} />
          새 스케줄 추가
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-card w-full max-w-md rounded-xl shadow-lg border p-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">새 스케줄 생성</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-muted-foreground hover:text-foreground"><X size={20}/></button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">스케줄 이름</label>
                <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="예: 매시간 뉴스 수집" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">실행 방식</label>
                <select className="w-full border rounded-md p-2 bg-transparent" value={formData.schedule_type} onChange={e => setFormData({...formData, schedule_type: e.target.value})}>
                  <option value="interval">주기적 실행 (알림 O)</option>
                  <option value="interval_silent">주기적 수집 (알림 X, DB저장만)</option>
                  <option value="digest">지정 시간 하루 요약 (단발성)</option>
                  <option value="window_digest">특정 시간대 집중 수집 & 요약</option>
                </select>
              </div>
              
              {formData.schedule_type.startsWith('interval') && (
                <div>
                  <label className="block text-sm font-medium mb-1">실행 주기 (분)</label>
                  <input required type="number" min="1" className="w-full border rounded-md p-2 bg-transparent" value={formData.interval_minutes} onChange={e => setFormData({...formData, interval_minutes: Number(e.target.value)})} />
                </div>
              )}

              {formData.schedule_type === 'digest' && (
                <div>
                  <label className="block text-sm font-medium mb-1">실행 시간 (Cron 표현식)</label>
                  <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="예: 0 16 * * * (매일 오후 4시)" value={formData.cron} onChange={e => setFormData({...formData, cron: e.target.value})} />
                  <p className="text-xs text-muted-foreground mt-1">기본값은 한국시간 기준 매일 오후 4시(16:00)입니다.</p>
                </div>
              )}

              {formData.schedule_type === 'window_digest' && (
                <div className="space-y-4 border p-4 rounded-lg bg-muted/20">
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="block text-sm font-medium mb-1">시작 시간 (시)</label>
                      <input required type="number" min="0" max="23" className="w-full border rounded-md p-2 bg-transparent" value={formData.start_hour} onChange={e => setFormData({...formData, start_hour: Number(e.target.value)})} />
                    </div>
                    <div className="flex-1">
                      <label className="block text-sm font-medium mb-1">요약 알림 시간 (종료 시)</label>
                      <input required type="number" min="0" max="23" className="w-full border rounded-md p-2 bg-transparent" value={formData.end_hour} onChange={e => setFormData({...formData, end_hour: Number(e.target.value)})} />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">시간대 내 수집 주기 (분)</label>
                    <input required type="number" min="1" className="w-full border rounded-md p-2 bg-transparent" value={formData.interval_minutes} onChange={e => setFormData({...formData, interval_minutes: Number(e.target.value)})} />
                    <p className="text-xs text-muted-foreground mt-1">
                      예: 3시 시작, 7시 종료, 10분 주기 👉 새벽 3시~6시 59분까지 10분마다 수집 후, 7시 정각에 요약 알림 전송
                    </p>
                  </div>
                </div>
              )}

              <button disabled={addMutation.isPending} type="submit" className="w-full bg-primary text-primary-foreground p-2 rounded-md font-bold mt-4 hover:bg-primary/90">
                {addMutation.isPending ? '생성 중...' : '생성하기'}
              </button>
            </form>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">로딩 중...</div>
      ) : schedules?.length === 0 ? (
        <div className="border-2 border-dashed border-muted rounded-xl p-12 text-center">
          <Calendar className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">등록된 스케줄이 없습니다</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6">원하는 시간에 뉴스를 수집하도록 스케줄을 생성하세요.</p>
          <button onClick={() => setIsModalOpen(true)} className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
            첫 스케줄 만들기
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {schedules?.map((schedule: any) => (
            <div key={schedule.id} className="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
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
                    <button onClick={() => runMutation.mutate(schedule.id)} className="p-2 text-muted-foreground hover:text-primary transition-colors bg-muted/50 rounded-md" title="지금 즉시 실행">
                      <PlayCircle size={18} />
                    </button>
                    <button onClick={() => deleteMutation.mutate(schedule.id)} className="p-2 text-muted-foreground hover:text-destructive transition-colors bg-muted/50 rounded-md">
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
