import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Send, Plus, Trash2, CheckCircle2, XCircle } from 'lucide-react';

export function Channels() {
  const { data: channels, isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: async () => {
      const { data } = await api.get('/channels');
      return data;
    },
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <Send className="text-primary" />
            알림 채널
          </h1>
          <p className="text-muted-foreground mt-2">텔레그램, 디스코드, 이메일 연동을 관리합니다.</p>
        </div>
        <button className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors">
          <Plus size={18} />
          채널 연결
        </button>
      </div>

      {isLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">로딩 중...</div>
      ) : channels?.length === 0 ? (
        <div className="border-2 border-dashed border-muted rounded-xl p-12 text-center">
          <Send className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">등록된 알림 채널이 없습니다</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6">수집된 뉴스를 받을 채널을 연동해주세요.</p>
          <button className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
            채널 연동하기
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {channels?.map((channel: any) => (
            <div key={channel.id} className="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="uppercase text-xs font-bold bg-muted px-2 py-1 rounded text-muted-foreground tracking-wider">
                      {channel.channel_type}
                    </span>
                    <h3 className="font-semibold">{channel.name}</h3>
                  </div>
                  <button className="text-muted-foreground hover:text-destructive transition-colors">
                    <Trash2 size={18} />
                  </button>
                </div>

                <div className="pt-4 border-t mt-4 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    {channel.is_active ? (
                      <><CheckCircle2 size={16} className="text-green-500" /> <span className="font-medium">활성</span></>
                    ) : (
                      <><XCircle size={16} className="text-muted-foreground" /> <span>비활성</span></>
                    )}
                  </div>
                  <button className="text-primary hover:underline text-sm font-medium">테스트 발송</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
