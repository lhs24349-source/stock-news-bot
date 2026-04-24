import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Tags, Plus, Trash2 } from 'lucide-react';

export function Keywords() {
  const { data: keywords, isLoading } = useQuery({
    queryKey: ['keywords'],
    queryFn: async () => {
      const { data } = await api.get('/keywords');
      return data;
    },
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <Tags className="text-primary" />
            키워드 그룹 관리
          </h1>
          <p className="text-muted-foreground mt-2">뉴스 알림을 받을 키워드 조건과 제외어를 설정합니다.</p>
        </div>
        <button className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors">
          <Plus size={18} />
          새 그룹 추가
        </button>
      </div>

      {isLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">로딩 중...</div>
      ) : keywords?.length === 0 ? (
        <div className="border-2 border-dashed border-muted rounded-xl p-12 text-center">
          <Tags className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">등록된 키워드 그룹이 없습니다</h3>
          <p className="text-sm text-muted-foreground mt-2 mb-6">첫 번째 키워드 그룹을 생성하고 알림을 받아보세요.</p>
          <button className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
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
                  <button className="text-muted-foreground hover:text-destructive transition-colors">
                    <Trash2 size={18} />
                  </button>
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

                  <div className="pt-4 border-t mt-4 flex items-center justify-between text-sm text-muted-foreground">
                    <span>유사도 임계값: <strong className="text-foreground">{group.threshold}%</strong></span>
                    <span>상태: {group.is_active ? <span className="text-green-500 font-medium">활성</span> : '비활성'}</span>
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
