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
    <div className="grid min-h-screen grid-cols-[236px_minmax(0,1fr)] tablet:grid-cols-[215px_minmax(0,1fr)] mobile:block">
      <a
        className="fixed -top-[100px] left-[10px] z-[100] bg-white p-[10px] focus:top-[10px] not-focus:h-px not-focus:w-px not-focus:overflow-hidden not-focus:p-0 not-focus:whitespace-nowrap not-focus:[clip-path:inset(50%)]"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content").focus();
        }}
      >
        Skip to content
      </a>
      <aside className="sticky top-0 flex h-screen flex-col border-r border-[#e1e6df] bg-white px-[22px] pt-[34px] pb-6 tablet:px-[17px] mobile:static mobile:h-auto mobile:border-r-0 mobile:border-b mobile:border-b-line mobile:px-5 mobile:pt-[22px] mobile:pb-[15px]">
        <Brand className="mobile:text-[1.55rem]" />
        <div className="mx-3 mt-[52px] mb-[14px] text-[0.7rem] font-bold tracking-[0.13em] text-[#5b7061] mobile:hidden">
          YOUR KITCHEN
        </div>
        <nav
          aria-label="Main navigation"
          className="grid gap-[5px] mobile:mt-[23px] mobile:flex mobile:flex-wrap mobile:gap-[5px]"
        >
          {sections.map(([key, label, icon]) => (
            <NavLink
              to={`/${key}`}
              key={key}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-[11px] px-[14px] py-3 text-[0.9rem] no-underline mobile:gap-[6px] mobile:px-[10px] mobile:py-2 mobile:text-[0.8rem] ${
                  isActive
                    ? "bg-[#e8f0e7] font-[650] text-green"
                    : "font-medium text-[#68766c] hover:bg-[#f3f6f1]"
                }`
              }
            >
              <Icon name={icon} className="mobile:h-[17px] mobile:w-[17px]" />
              {label}
              {key === "fridge" && (
                <span
                  className="ml-auto rounded-[6px] bg-[#d4e4d5] px-[7px] py-px text-[0.75rem] mobile:hidden"
                  aria-hidden="true"
                >
                  {data.inventory.length}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto flex gap-[10px] border-t border-[#e7ebe5] pt-[22px] mobile:mt-[17px] mobile:pt-3">
          <span className="grid h-[35px] w-[35px] shrink-0 place-items-center rounded-[50%] bg-[#ece6dc] text-[0.9rem] font-bold text-[#6b624a] mobile:h-[29px] mobile:w-[29px]">
            {session.email[0].toUpperCase()}
          </span>
          <div className="min-w-0 text-[0.75rem] mobile:flex mobile:flex-1 mobile:items-center mobile:justify-between mobile:gap-4">
            <span
              className="block overflow-hidden text-ellipsis whitespace-nowrap"
              title={session.email}
            >
              {session.email}
            </span>
            <button
              className="shrink-0 bg-transparent px-0 py-[2px] text-[0.8rem] whitespace-nowrap text-[#66756a] underline"
              onClick={() => clearSession()}
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>
      <main
        id="main-content"
        tabIndex="-1"
        className="m-auto min-h-screen w-full max-w-[1320px] px-12 pt-[38px] pb-0 wide:px-[70px] tablet:px-7 tablet:pt-[30px] mobile:px-5 mobile:pt-[26px]"
        aria-busy={busy || loading}
      >
        <header className="mb-[30px] flex items-center justify-between gap-5 mobile:mb-6">
          <div>
            <span className="eyebrow mb-[9px] text-[0.65rem] text-[#5c7060]">
              LESS WASTE. MORE TASTE.
            </span>
            <h1 className="mobile:text-[2rem]">{section[1]}</h1>
          </div>
          <span className="flex items-center gap-2 text-[0.8rem] text-[#586d5d] tablet:hidden">
            <Icon className="w-[17px]" />A little better, every day.
          </span>
        </header>
        {error && !selected && (
          <div className="alert-error message" role="alert">
            {error}
            <button
              className="btn-text shrink-0"
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
          <div className="alert-success message" role="status">
            {notice}
          </div>
        )}
        {loading ? (
          <div className="px-5 py-[100px] text-center text-muted" role="status">
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
            className="m-0 min-w-0 border-0 p-0"
            aria-label="Kitchen actions"
            disabled={busy}
          >
            <Outlet context={kitchen} />
          </fieldset>
        )}
        <footer className="flex items-center justify-between gap-5 pt-[42px] pb-[25px] text-[0.75rem] text-[#5c7060] mobile:flex-col mobile:items-start mobile:gap-[15px] mobile:pt-8">
          <Brand small />
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
