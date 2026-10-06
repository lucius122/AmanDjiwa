import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Button } from '../../components/Button';
import { Icon } from '../../components/Icon';
import { useToast } from '../../components/Toast';
import { copy } from '../../lib/copy';
import { clockDot, fromWib, todayWib, weekdayShort } from '../../lib/time';
import type { FollowUp } from '../../lib/types';
import { staffApi } from '../../lib/api';

const t = copy.schedule;
const FIELD = 'h-48 rounded-12 border-1.5 border-sand-400 bg-cream px-14 text-15';
const schema = z
  .object({
    title: z.string().trim().min(1).max(200),
    date: z.string().min(1),
    start: z.string().min(1),
    end: z.string(),
  })
  .refine((v) => !v.end || v.end > v.start, { path: ['end'] });
type Form = z.infer<typeof schema>;

const dayOfMonth = (d: Date) => new Intl.DateTimeFormat('id-ID', { day: 'numeric', timeZone: 'Asia/Jakarta' }).format(d);

export function Schedule() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ['follow-ups'], queryFn: () => staffApi<FollowUp[]>('/follow-ups') });
  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { title: '', date: todayWib(), start: '', end: '' },
  });
  const add = useMutation({
    mutationFn: (v: Form) =>
      staffApi<FollowUp>('/follow-ups', {
        method: 'POST',
        body: {
          title: v.title,
          scheduled_at: fromWib(v.date, v.start).toISOString(),
          ends_at: v.end ? fromWib(v.date, v.end).toISOString() : null,
        },
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      form.reset({ title: '', date: form.getValues('date'), start: '', end: '' });
      toast(t.saved);
    },
    onError: () => toast(t.failed),
  });
  const remove = useMutation({
    mutationFn: (id: string) => staffApi<void>(`/follow-ups/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      toast(t.removed);
    },
    onError: () => toast(t.failed),
  });
  const err = form.formState.errors;

  return (
    <div className="flex max-w-720 flex-1 flex-col gap-12 overflow-y-auto px-18 py-22">
      <h1 className="m-0 mb-4 text-22 font-extrabold">{t.title}</h1>
      {list.data?.map((j) => {
        const start = new Date(j.scheduled_at);
        return (
          <div key={j.id} className="flex items-center gap-14 rounded-14 border border-sand-200 bg-white p-16">
            <div className="flex w-56 flex-none flex-col items-center rounded-12 bg-teal-100 py-6">
              <span className="text-11 font-bold text-teal-800">{weekdayShort(start)}</span>
              <span className="text-20 font-extrabold">{dayOfMonth(start)}</span>
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <span className="text-15 font-bold">{j.title}</span>
              <span className="text-13 text-muted">
                {clockDot(start)}
                {j.ends_at ? ` – ${clockDot(new Date(j.ends_at))}` : ''}
              </span>
            </div>
            {/* DESIGN-GAP: hapus jadwal tidak ada di desain. */}
            <button
              type="button"
              aria-label={t.remove(j.title)}
              disabled={remove.isPending}
              onClick={() => remove.mutate(j.id)}
              className="flex h-44 w-44 flex-none items-center justify-center rounded-12 bg-transparent hover:bg-cream"
            >
              <Icon name="trash" className="h-20 w-20 stroke-muted" />
            </button>
          </div>
        );
      })}
      {list.isSuccess && list.data.length === 0 && <p className="m-0 text-14 text-muted">{t.empty}</p>}
      {list.isError && <p className="m-0 text-14 text-muted">{copy.staff.loadFailed}</p>}

      {/* DESIGN-GAP: form tambah jadwal (desain hanya menampilkan daftar); gaya dari kartu Catatan. */}
      <form
        onSubmit={form.handleSubmit((v) => add.mutate(v))}
        noValidate
        className="mt-8 flex flex-col gap-12 rounded-16 border border-sand-200 bg-white px-18 py-16"
      >
        <span className="text-14 font-bold">{t.add}</span>
        <label className="flex flex-col gap-6 text-13 font-semibold">
          {t.titleLabel}
          <input {...form.register('title')} maxLength={200} placeholder={t.titlePlaceholder} aria-invalid={!!err.title} className={FIELD} />
        </label>
        <div className="grid grid-cols-fit-150 gap-10">
          <label className="flex flex-col gap-6 text-13 font-semibold">
            {t.date}
            <input type="date" {...form.register('date')} min={todayWib()} className={FIELD} />
          </label>
          <label className="flex flex-col gap-6 text-13 font-semibold">
            {t.start}
            <input type="time" {...form.register('start')} aria-invalid={!!err.start} className={FIELD} />
          </label>
          <label className="flex flex-col gap-6 text-13 font-semibold">
            {t.end}
            <input type="time" {...form.register('end')} aria-invalid={!!err.end} className={`${FIELD} ${err.end ? 'border-warn' : ''}`} />
          </label>
        </div>
        <Button type="submit" disabled={add.isPending} className="self-start px-20">
          {t.save}
        </Button>
      </form>
    </div>
  );
}
