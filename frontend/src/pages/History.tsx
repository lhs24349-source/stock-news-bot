import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { History as HistoryIcon, Search, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';

export function History() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [sort, setSort] = useState('time_desc');
  const pageSize = 30;

  const { data, isLoading, isError } = useQuery({
    queryKey: ['news', page, search, sort],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        sort: sort,
      });
      if (search) params.set('search', search);
      const { data } = await api.get(`/news?${params.toString()}`);
      return data;
    },
  });

  // 검색 폼 제출 핸들러
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1); // 검색 시 첫 페이지로 이동
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <HistoryIcon className="text-primary" />
            수집된 뉴스 내역
          </h1>
          <p className="text-muted-foreground mt-2">
            {data?.total ? `총 ${data.total}건의 뉴스가 수집되었습니다.` : '최근 수집되어 매칭된 주요 뉴스 목록입니다.'}
          </p>
        </div>

        {/* 검색 & 정렬 폼 */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setPage(1);
            }}
            className="h-10 px-3 py-2 rounded-md border border-input bg-transparent text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="time_desc">최신순</option>
            <option value="time_asc">과거순</option>
            <option value="title_asc">제목순</option>
            <option value="keyword_asc">키워드순</option>
          </select>
          <form onSubmit={handleSearch} className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="뉴스 제목 검색..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full h-10 pl-9 pr-4 rounded-md border border-input bg-transparent text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </form>
        </div>
      </div>

      {/* 뉴스 목록 */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-muted-foreground">로딩 중...</div>
        ) : isError ? (
          <div className="p-12 text-center text-destructive font-medium">서버와 연결할 수 없습니다.</div>
        ) : !data?.items?.length ? (
          <div className="p-12 text-center text-muted-foreground">
            <HistoryIcon className="mx-auto h-10 w-10 mb-3 opacity-40" />
            <p className="text-lg font-medium">수집된 뉴스 내역이 없습니다.</p>
            <p className="text-sm mt-1">스케줄을 등록하면 자동으로 뉴스가 수집됩니다.</p>
          </div>
        ) : (
          <>
            {/* 뉴스 리스트 (스크롤 가능) */}
            <div className="divide-y max-h-[calc(100vh-340px)] overflow-y-auto">
              {data.items.map((news: any) => (
                <div key={news.id} className="p-5 hover:bg-muted/50 transition-colors group">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                    <div className="flex-1 space-y-1.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider">
                          {news.source}
                        </span>
                        {news.keyword_group && (
                          <span className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-0.5 rounded text-xs font-medium">
                            {news.keyword_group}
                          </span>
                        )}
                        {news.matched_keyword && (
                          <span className="text-xs text-muted-foreground">
                            매칭: <strong>{news.matched_keyword}</strong>
                            {news.match_score && ` (${Math.round(news.match_score)}%)`}
                          </span>
                        )}
                      </div>
                      <a
                        href={news.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-base font-medium leading-snug hover:underline flex items-start gap-2 group-hover:text-primary transition-colors"
                      >
                        {news.title}
                        <ExternalLink size={14} className="mt-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </a>
                      {news.summary && (
                        <p className="text-sm text-muted-foreground line-clamp-2">{news.summary}</p>
                      )}
                    </div>

                    <div className="flex flex-col items-start md:items-end text-sm text-muted-foreground whitespace-nowrap shrink-0">
                      {news.published_at ? (
                        <>
                          <span>{format(new Date(news.published_at), 'yyyy-MM-dd')}</span>
                          <span className="font-medium">{format(new Date(news.published_at), 'HH:mm:ss')}</span>
                        </>
                      ) : (
                        <span>시간 미확인</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="border-t p-4 flex items-center justify-between bg-muted/10">
                <span className="text-sm text-muted-foreground">
                  {data.total}건 중 {(page - 1) * pageSize + 1}~{Math.min(page * pageSize, data.total)}건
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="p-2 rounded-md border hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="text-sm font-medium px-2">
                    {page} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="p-2 rounded-md border hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
