import { Navigate, Outlet, useLocation } from "react-router-dom";

// Personal screens require a signed session. Without one the user is sent to
// sign-in and returned to the requested screen afterwards.
export default function ProtectedRoute({ session }) {
  const location = useLocation();
  if (!session)
    return (
      <Navigate to="/sign-in" replace state={{ from: location.pathname }} />
    );
  return <Outlet />;
}
