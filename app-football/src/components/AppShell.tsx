import { Clock3, Home, Newspaper, ShieldCheck } from "lucide-react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const routeTitles: Record<string, string> = {
  "/": "Football TG",
  "/news": "Новости",
  "/rubric": "Рубрика"
};

function getPageTitle(pathname: string) {
  if (pathname.startsWith("/news")) {
    return routeTitles["/news"];
  }

  if (pathname.startsWith("/rubric")) {
    return routeTitles["/rubric"];
  }

  return routeTitles["/"];
}

export function AppShell() {
  const location = useLocation();
  const pageTitle = getPageTitle(location.pathname);
  const { user } = useAuth();
  const userLabel = user?.username ? `@${user.username}` : `id ${user?.id ?? "n/a"}`;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__row">
          <div>
            <Link className="brand" to="/">
              Football TG
            </Link>
            <h1 className="page-title">{pageTitle}</h1>
          </div>
          <div className="status-cluster">
            <span className="pill pill--neutral">
              <ShieldCheck size={14} />
              {userLabel}
            </span>
            <span className="pill pill--neutral">
              <Clock3 size={14} />
              sync 2h
            </span>
          </div>
        </div>
      </header>

      <main className="content">
        <Outlet />
      </main>

      <nav className="bottom-nav" aria-label="Основная навигация">
        <NavLink
          className={({ isActive }) =>
            `bottom-nav__item${isActive ? " bottom-nav__item--active" : ""}`
          }
          end
          to="/"
        >
          <Home size={18} />
          <span>Главная</span>
        </NavLink>
        <NavLink
          className={({ isActive }) =>
            `bottom-nav__item${isActive ? " bottom-nav__item--active" : ""}`
          }
          to="/news"
        >
          <Newspaper size={18} />
          <span>Новости</span>
        </NavLink>
      </nav>
    </div>
  );
}
