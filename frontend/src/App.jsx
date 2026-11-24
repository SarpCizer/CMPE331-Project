import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { useKitchen } from "./hooks/useKitchen";
import Auth from "./pages/Auth";
import Favorites from "./pages/Favorites";
import Fridge from "./pages/Fridge";
import History from "./pages/History";
import Preferences from "./pages/Preferences";
import Recipes from "./pages/Recipes";
import Shopping from "./pages/Shopping";

function SignIn({ kitchen }) {
  const { state } = useLocation();
  const from = state?.from && state.from !== "/sign-in" ? state.from : "/fridge";
  if (kitchen.session) return <Navigate to={from} replace />;
  return (
    <Auth
      key={kitchen.notice}
      onSession={kitchen.signIn}
      notice={kitchen.notice}
    />
  );
}

export default function App() {
  const kitchen = useKitchen();
  return (
    <Routes>
      <Route path="/sign-in" element={<SignIn kitchen={kitchen} />} />
      <Route element={<ProtectedRoute session={kitchen.session} />}>
        <Route element={<Layout kitchen={kitchen} />}>
          <Route index element={<Navigate to="/fridge" replace />} />
          <Route path="fridge" element={<Fridge />} />
          <Route path="recipes" element={<Recipes />} />
          <Route path="shopping" element={<Shopping />} />
          <Route path="favorites" element={<Favorites />} />
          <Route path="history" element={<History />} />
          <Route path="preferences" element={<Preferences />} />
          <Route path="*" element={<Navigate to="/fridge" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
