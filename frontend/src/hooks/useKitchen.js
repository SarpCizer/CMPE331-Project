import { useEffect, useRef, useState } from "react";
import { createApi } from "../api";
import { initialData, initialResources, paths } from "../constants";
import { savedSession } from "../utils/session";

// Session, server collections and the shared mutation runner for the kitchen UI.
export function useKitchen() {
  const [session, setSession] = useState(savedSession),
    [data, setData] = useState(initialData),
    [generated, setGenerated] = useState([]),
    [selected, setSelected] = useState(null),
    [busy, setBusy] = useState(false),
    [resources, setResources] = useState(() => initialResources(!!session)),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const generation = useRef(0),
    controller = useRef(new AbortController()),
    busyRef = useRef(false);
  const api = createApi(session?.token, controller.current.signal);
  function clearSession(message = "") {
    generation.current++;
    controller.current.abort();
    controller.current = new AbortController();
    busyRef.current = false;
    sessionStorage.removeItem("fridgely.session");
    setSession(null);
    setData(initialData());
    setGenerated([]);
    setSelected(null);
    setBusy(false);
    setResources(initialResources());
    setError("");
    setNotice(message);
  }
  function signIn(value) {
    clearSession();
    sessionStorage.setItem("fridgely.session", JSON.stringify(value));
    setSession(value);
    setResources(initialResources(true));
    setNotice("");
  }
  async function loadResources(request, keys, version = generation.current) {
    setResources((value) => ({
      ...value,
      ...Object.fromEntries(
        keys.map((key) => [key, { pending: true, error: "" }]),
      ),
    }));
    const results = await Promise.all(
      keys.map(async (key) => {
        try {
          const result = await request(paths[key]);
          if (version !== generation.current) return false;
          setData((value) => ({ ...value, [key]: result }));
          setResources((value) => ({
            ...value,
            [key]: { pending: false, error: "" },
          }));
          return true;
        } catch (error) {
          if (version !== generation.current || error.name === "AbortError")
            return false;
          if (error.status === 401)
            clearSession("Your session ended. Please sign in again.");
          else
            setResources((value) => ({
              ...value,
              [key]: { pending: false, error: error.message },
            }));
          return false;
        }
      }),
    );
    return results.every(Boolean);
  }
  useEffect(() => {
    if (!session) return;
    const version = generation.current,
      request = createApi(session.token, controller.current.signal);
    void loadResources(request, Object.keys(paths), version);
  }, [session]);
  async function run(operation, message, refresh = []) {
    if (busyRef.current) return false;
    const version = generation.current;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await operation();
      if (version !== generation.current) return false;
      const refreshed = await loadResources(api, refresh, version);
      if (version !== generation.current) return false;
      if (message)
        setNotice(
          refreshed
            ? message
            : `${message} Some saved data could not be refreshed. Use Retry to load it again.`,
        );
      return result ?? true;
    } catch (error) {
      if (version !== generation.current || error.name === "AbortError")
        return false;
      if (error.status === 401)
        clearSession("Your session ended. Please sign in again.");
      else setError(error.message);
      return false;
    } finally {
      if (version === generation.current) {
        busyRef.current = false;
        setBusy(false);
      }
    }
  }
  async function openRecipe(id) {
    const recipe = await run(() => api(`/recipes/${id}`), "", ["history"]);
    if (recipe && typeof recipe === "object") setSelected(recipe);
  }
  return {
    session,
    data,
    generated,
    setGenerated,
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
    signIn,
    loadResources,
    run,
    openRecipe,
  };
}
