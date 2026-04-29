import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Send, MessageSquare, Plus, Trash2, CheckCircle2, XCircle, X } from 'lucide-react';

export function Channels() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', channel_type: 'telegram', token: '', chat_id: '', webhook_url: '' });

  const { data: channels, isLoading, isError } = useQuery({
    queryKey: ['channels'],
    queryFn: async () => {
      const { data } = await api.get('/channels');
      return data;
    },
  });

  const addMutation = useMutation({
    mutationFn: async (newData: any) => {
      await api.post('/channels', newData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      setIsModalOpen(false);
      setFormData({ name: '', channel_type: 'telegram', token: '', chat_id: '', webhook_url: '' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      if (confirm('알림 채널을 삭제하시겠습니까?')) await api.delete(`/channels/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] })
  });

  const testMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/channels/${id}/test`);
      alert('테스트 메시지를 전송했습니다. 채널을 확인해주세요!');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: formData.name,
      channel_type: formData.channel_type,
      config: formData.channel_type === 'telegram' 
        ? { bot_token: formData.token, chat_id: formData.chat_id } 
        : { webhook_url: formData.webhook_url },
      is_active: true
    };
    addMutation.mutate(payload);
  };

  return (
    <div className="space-y-8 relative">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <MessageSquare className="text-primary" />
            알림 채널 관리
          </h1>
          <p className="text-muted-foreground mt-2">뉴스 요약을 받을 텔레그램, 디스코드 채널을 설정합니다.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors"
        >
          <Plus size={18} />
          새 채널 추가
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-card w-full max-w-md rounded-xl shadow-lg border p-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">새 알림 채널 추가</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-muted-foreground hover:text-foreground"><X size={20}/></button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">채널 이름</label>
                <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="예: 개인 텔레그램" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">플랫폼</label>
                <select className="w-full border rounded-md p-2 bg-transparent" value={formData.channel_type} onChange={e => setFormData({...formData, channel_type: e.target.value as 'telegram' | 'discord'})}>
                  <option value="telegram">Telegram</option>
                  <option value="discord">Discord</option>
                </select>
              </div>
              
              {formData.channel_type === 'telegram' ? (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Bot Token</label>
                    <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="BotFather에서 발급받은 봇 토큰" value={formData.token} onChange={e => setFormData({...formData, token: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Chat ID</label>
                    <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="숫자로 된 Chat ID (예: 123456789)" value={formData.chat_id} onChange={e => setFormData({...formData, chat_id: e.target.value})} />
                    <p className="text-xs text-muted-foreground mt-1">
                      개인 채팅방의 경우 숫자 ID를 기입하세요. (확인 봇: @userinfobot)
                    </p>
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-sm font-medium mb-1">Webhook URL</label>
                  <input required type="url" className="w-full border rounded-md p-2 bg-transparent" placeholder="https://discord.com/api/webhooks/..." value={formData.webhook_url} onChange={e => setFormData({...formData, webhook_url: e.target.value})} />
                </div>
              )}

              <button disabled={addMutation.isPending} type="submit" className="w-full bg-primary text-primary-foreground p-2 rounded-md font-bold mt-4 hover:bg-primary/90">
                {addMutation.isPending ? '연결 중...' : '연결하기'}
              </button>
            </form>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">로딩 중...</div>
      ) : isError ? (
        <div className="h-40 flex items-center justify-center text-destructive font-medium">서버와 연결할 수 없습니다.</div>
      ) : (!channels || channels.length === 0) ? (
        <div className="border-2 border-dashed border-muted rounded-xl p-12 text-center">
          <Send className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">등록된 알림 채널이 없습니다</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6">수집된 뉴스를 받을 채널을 연동해주세요.</p>
          <button onClick={() => setIsModalOpen(true)} className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
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
                  <button onClick={() => deleteMutation.mutate(channel.id)} className="text-muted-foreground hover:text-destructive transition-colors">
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
                  <button onClick={() => testMutation.mutate(channel.id)} className="text-primary hover:underline text-sm font-medium">테스트 발송</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
