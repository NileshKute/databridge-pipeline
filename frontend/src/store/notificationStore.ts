import { create } from "zustand";
import apiClient from "@/api/client";
import type { Notification, NotificationListResponse } from "@/types";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;

  fetchNotifications: () => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllRead: () => Promise<void>;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  fetchNotifications: async () => {
    set({ isLoading: true });
    try {
      const { data } = await apiClient.get<NotificationListResponse>(
        "/notifications/",
        { params: { per_page: 50 } },
      );
      set({
        notifications: data.items,
        unreadCount: data.unread_count,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const { data } = await apiClient.get<{ count: number }>(
        "/notifications/unread/count",
      );
      set({ unreadCount: data.count });
    } catch {
      // Non-critical
    }
  },

  markAsRead: async (id) => {
    try {
      await apiClient.put(`/notifications/${id}/read`);
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, is_read: true } : n,
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch {
      // Retry silently
    }
  },

  markAllRead: async () => {
    try {
      await apiClient.put("/notifications/read-all");
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
        unreadCount: 0,
      }));
    } catch {
      // Retry silently
    }
  },
}));
