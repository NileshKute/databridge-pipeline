import { Link } from "react-router-dom";
import { Home } from "lucide-react";

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center px-4">
      <h1 className="text-6xl font-bold text-surface-600 mb-2">404</h1>
      <p className="text-xl text-surface-300 mb-6">Page not found</p>
      <Link to="/" className="btn-primary flex items-center gap-2">
        <Home className="h-4 w-4" />
        Back to Dashboard
      </Link>
    </div>
  );
}
