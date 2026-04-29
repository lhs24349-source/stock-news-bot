import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Tags, Plus, Trash2, X, Pencil } from 'lucide-react';

export function Keywords() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({ name: '', keywords: '', exclude_keywords: '' });

  const { data: keywords, isLoading, isError } = useQuery({
    queryKey: ['keywords'],
    queryFn: async () => {
      const { data } = await api.get('/keywords');
      return data;
    },
  });

  // ... (addMutation 등 그대로 유지) ...

  const addMutation = useMutation({
    mutationFn: async (newData: any) => {
      await api.post('/keywords', newData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keywords'] });
      closeModal();
    }
  });

  const updateMutation = useMutation({
    mutationFn: async (data: { id: number, payload: any }) => {
      await api.put(`/keywords/${data.id}`, data.payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keywords'] });
      closeModal();
    }
  });

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingId(null);
    setFormData({ name: '', keywords: '', exclude_keywords: '' });
  };

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      if (confirm('정말 삭제하시겠습니까?')) {
        await api.delete(`/keywords/${id}`);
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['keywords'] })
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: formData.name,
      keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
      exclude_keywords: formData.exclude_keywords.split(',').map(k => k.trim()).filter(k => k),
    };

    if (editingId) {
      updateMutation.mutate({ id: editingId, payload });
    } else {
      addMutation.mutate(payload);
    }
  };

  const openEditModal = (group: any) => {
    setFormData({
      name: group.name,
      keywords: group.keywords.join(', '),
      exclude_keywords: group.exclude_keywords?.join(', ') || ''
    });
    setEditingId(group.id);
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-8 relative">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <Tags className="text-primary" />
            키워드 그룹 관리
          </h1>
          <p className="text-muted-foreground mt-2">뉴스 알림을 받을 키워드 조건과 제외어를 설정합니다.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors"
        >
          <Plus size={18} />
          새 그룹 추가
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-card w-full max-w-md rounded-xl shadow-lg border p-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">{editingId ? '키워드 그룹 수정' : '새 키워드 그룹 추가'}</h2>
              <button onClick={closeModal} className="text-muted-foreground hover:text-foreground"><X size={20}/></button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">그룹 이름</label>
                <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="예: 반도체 호재" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">포함 키워드 (쉼표로 구분)</label>
                <input required type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="예: HBM, 엔비디아, 삼성전자" value={formData.keywords} onChange={e => setFormData({...formData, keywords: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">제외 키워드 (쉼표로 구분)</label>
                <input type="text" className="w-full border rounded-md p-2 bg-transparent" placeholder="예: 광고, 찌라시" value={formData.exclude_keywords} onChange={e => setFormData({...formData, exclude_keywords: e.target.value})} />
              </div>
              <button disabled={addMutation.isPending || updateMutation.isPending} type="submit" className="w-full bg-primary text-primary-foreground p-2 rounded-md font-bold mt-4 hover:bg-primary/90">
                {(addMutation.isPending || updateMutation.isPending) ? '저장 중...' : '저장하기'}
              </button>
            </form>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">로딩 중...</div>
      ) : isError ? (
        <div className="h-40 flex items-center justify-center text-destructive font-medium">서버와 연결할 수 없습니다. (CORS 또는 API URL 확인)</div>
      ) : (!keywords || keywords.length === 0) ? (
        <div className="border-2 border-dashed border-muted rounded-xl p-12 text-center">
          <Tags className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">등록된 키워드 그룹이 없습니다</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6">첫 번째 키워드 그룹을 생성하고 알림을 받아보세요.</p>
          <button onClick={() => setIsModalOpen(true)} className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
            키워드 그룹 생성
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {keywords?.map((group: any) => (
            <div key={group.id} className="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg">{group.name}</h3>
                  <div className="flex gap-2">
                    <button onClick={() => openEditModal(group)} className="text-muted-foreground hover:text-primary transition-colors">
                      <Pencil size={18} />
                    </button>
                    <button onClick={() => deleteMutation.mutate(group.id)} className="text-muted-foreground hover:text-destructive transition-colors">
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">포함 키워드</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {group.keywords.map((kw: string) => (
                        <span key={kw} className="bg-primary/10 text-primary px-2.5 py-1 rounded-md text-sm font-medium">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {group.exclude_keywords?.length > 0 && (
                    <div>
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">제외 키워드</span>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {group.exclude_keywords.map((kw: string) => (
                          <span key={kw} className="bg-destructive/10 text-destructive px-2.5 py-1 rounded-md text-sm font-medium">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
