import { useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { pageResources, paths, resourceLabels, sections } from "../constants";
import Brand from "./Brand";
import Icon from "./Icon";
import RecipeDialog from "./RecipeDialog";
import ResourceError from "./ResourceError";

// Signed-in application shell: navigation, page header, shared messages,
// per-page loading/error states and the recipe details dialog.
export default function Layout({ kitchen }) {
  const {
    session,
    data,
    selected,
    setSelected,
    busy,
    resources,
    error,
    setError,
    notice,
    setNotice,
    api,
    clearSession,
    loadResources,
    run,
  } = kitchen;
  const { pathname } = useLocation();
  const page = pathname.slice(1);
  const firstRender = useRef(true);
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    setNotice("");
    setError("");
  }, [pathname]);
  const section = sections.find((s) => s[0] === page) || sections[0];
  const resource = pageResources[section[0]],
    state = resources[resource],
    loading = state.pending;
  return (
    <div className="app-layout">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content").focus();
        }}
      >
        Skip to content
      </a>
      <aside className="sidebar">
        <Brand />
        <div className="nav-caption">YOUR KITCHEN</div>
        <nav aria-label="Main navigation">
          {sections.map(([key, label, icon]) => (
            <NavLink
              to={`/${key}`}
              key={key}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <Icon name={icon} />
              {label}
              {key === "fridge" && (
                <span className="nav-count" aria-hidden="true">
                  {data.inventory.length}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="avatar">{session.email[0].toUpperCase()}</span>
          <div className="account">
            <span title={session.email}>{session.email}</span>
            <button onClick={() => clearSession()}>Sign out</button>
          </div>
        </div>
      </aside>
      <main
        id="main-content"
        tabIndex="-1"
        className="main"
        aria-busy={busy || loading}
      >
        <header className="page-header">
          <div>
            <span className="eyebrow">LESS WASTE. MORE TASTE.</span>
            <h1>{section[1]}</h1>
          </div>
          <span className="header-note">
            <Icon />A little better, every day.
          </span>
        </header>
        {error && !selected && (
          <div className="message error" role="alert">
            {error}
            <button
              className="text-button"
              disabled={busy}
              onClick={() =>
                run(async () => true, "Data refreshed.", Object.keys(paths))
              }
            >
              Refresh data
            </button>
          </div>
        )}
        {notice && !selected && (
          <div className="message success" role="status">
            {notice}
          </div>
        )}
        {loading ? (
          <div className="loading" role="status">
            Loading {resourceLabels[resource].toLowerCase()}…
          </div>
        ) : state.error ? (
          <ResourceError
            label={resourceLabels[resource]}
            error={state.error}
            retry={() => loadResources(api, [resource])}
            busy={busy}
          />
        ) : (
          <fieldset
            className="content-fieldset"
            aria-label="Kitchen actions"
            disabled={busy}
          >
            <Outlet context={kitchen} />
          </fieldset>
        )}
        <footer className="page-footer">
          <Brand />
          <span>A little less waste. A lot more possibility.</span>
          <a href="/api/docs">API documentation</a>
        </footer>
      </main>
      {selected && (
        <RecipeDialog
          recipe={selected}
          favorites={data.favorites}
          favoriteState={resources.favorites}
          retryFavorites={() => loadResources(api, ["favorites"])}
          busy={busy}
          error={error}
          notice={notice}
          onClose={() => setSelected(null)}
          run={run}
          api={api}
        />
      )}
    </div>
  );
}
