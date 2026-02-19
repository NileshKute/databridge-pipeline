import { Routes, Route, Navigate } from "react-router-dom";

import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import TransfersPage from "@/pages/TransfersPage";
import TransferDetailPage from "@/pages/TransferDetailPage";
import UploadPage from "@/pages/UploadPage";
import ApprovalsPage from "@/pages/ApprovalsPage";
import NotificationsPage from "@/pages/NotificationsPage";
import ActivityPage from "@/pages/ActivityPage";
import NotFoundPage from "@/pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="transfers" element={<TransfersPage />} />
        <Route path="transfers/:id" element={<TransferDetailPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="activity" element={<ActivityPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
