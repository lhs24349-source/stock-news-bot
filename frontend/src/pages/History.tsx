import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { History as HistoryIcon, Search, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';

export function History() {
  const { data, isLoading } = useQuery({
    queryKey: ['news'],
    queryFn: async () => {
      const { data } = await api.get('/news?limit=50');
      return data;
    },
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <HistoryIcon className="text-primary" />
            수집된 뉴스 내역
          </h1>
          <p className="text-muted-foreground mt-2">최근 수집되어 매칭된 주요 뉴스 목록입니다.</p>
        </div>
        
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="뉴스 검색..." 
            className="w-full h-10 pl-9 pr-4 rounded-md border border-input bg-transparent text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
        </div>
      </div>

      <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-muted-foreground">로딩 중...</div>
        ) : data?.items?.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground">
            수집된 뉴스 내역이 없습니다.
          </div>
        ) : (
          <div className="divide-y">
            {data?.items.map((news: any) => (
              <div key={news.id} className="p-6 hover:bg-muted/50 transition-colors group">
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider">
                        {news.source}
                      </span>
                      {news.matched_keywords && (
                        <span className="text-xs text-muted-foreground">
                          매칭: {news.matched_keywords}
                        </span>
                      )}
                    </div>
                    <a 
                      href={news.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-lg font-medium leading-tight hover:underline flex items-start gap-2 group-hover:text-primary transition-colors"
                    >
                      {news.title}
                      <ExternalLink size={14} className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  </div>
                  
                  <div className="flex flex-col items-start md:items-end text-sm text-muted-foreground whitespace-nowrap">
                    <span>{format(new Date(news.published_at), 'yyyy-MM-dd')}</span>
                    <span className="font-medium">{format(new Date(news.published_at), 'HH:mm:ss')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
