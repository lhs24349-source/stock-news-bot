import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Keywords } from './pages/Keywords';
import { Channels } from './pages/Channels';
import { Schedule } from './pages/Schedule';
import { History } from './pages/History';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="keywords" element={<Keywords />} />
          <Route path="channels" element={<Channels />} />
          <Route path="schedule" element={<Schedule />} />
          <Route path="history" element={<History />} />
          <Route path="*" element={<div className="p-8 text-center text-muted-foreground">준비 중인 페이지입니다.</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
