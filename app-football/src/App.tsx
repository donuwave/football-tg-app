import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { NewsPage } from "./pages/NewsPage";
import { RubricPage } from "./pages/RubricPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />} path="/">
        <Route element={<HomePage />} index />
        <Route element={<NewsPage />} path="news" />
        <Route element={<NewsPage />} path="news/:newsId" />
        <Route element={<RubricPage />} path="rubric" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Route>
    </Routes>
  );
}
