import { Navigate } from "react-router-dom";
import type { JSX } from "react";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-slate-500">Загрузка…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
