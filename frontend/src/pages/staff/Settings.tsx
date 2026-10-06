import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../components/Toast';
import { copy } from '../../lib/copy';
import type { StaffSettings } from '../../lib/types';
import { staffApi } from '../../lib/api';
import { useStaff } from './StaffApp';

const t = copy.staffSettings;

export function Settings() {
  const { settings } = useStaff();
  const toast = useToast();
  const queryClient = useQueryClient();
  const save = useMutation({
    mutationFn: (s: StaffSettings) => staffApi<StaffSettings>('/auth/staff/settings', { method: 'PUT', body: s }),
    onMutate: (s) => {
      const before = queryClient.getQueryData<StaffSettings>(['staff-settings']);
      queryClient.setQueryData(['staff-settings'], s);
      return before;
    },
    onError: (_e, _s, before) => {
      queryClient.setQueryData(['staff-settings'], before);
      toast(t.failed);
    },
  });

  return (
    <div className="flex max-w-720 flex-1 flex-col gap-12 overflow-y-auto px-18 py-22">
      <h1 className="m-0 mb-4 text-22 font-extrabold">{t.title}</h1>
      {(Object.keys(t.items) as (keyof StaffSettings)[]).map((k) => {
        const on = settings[k];
        return (
          <button
            key={k}
            type="button"
            role="switch"
            aria-checked={on}
            onClick={() => {
              if (k === 'notif_red' && !on && 'Notification' in window) void Notification.requestPermission();
              save.mutate({ ...settings, [k]: !on });
            }}
            className="flex items-center gap-14 rounded-14 border border-sand-200 bg-white p-16 text-left"
          >
            <span className="flex flex-1 flex-col gap-2">
              <span className="text-15 font-bold">{t.items[k].title}</span>
              <span className="text-13 text-muted">{t.items[k].body}</span>
            </span>
            <span
              className={`flex h-28 w-48 flex-none rounded-full p-3 transition-colors duration-200 ${on ? 'justify-end bg-teal-600' : 'justify-start bg-sand-500'}`}
            >
              <span className="h-22 w-22 rounded-full bg-white" />
            </span>
          </button>
        );
      })}
    </div>
  );
}
