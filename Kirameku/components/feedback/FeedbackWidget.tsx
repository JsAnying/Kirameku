"use client";

import { useRef, useState, type FormEvent } from "react";
import { CheckCircle2, Loader2, MessageSquarePlus, Send, X } from "lucide-react";
import { submitFeedback, type FeedbackType } from "@/app/api/feedback";
import { ApiError } from "@/app/api/client";

export default function FeedbackWidget() {
  const dialog = useRef<HTMLDialogElement>(null);
  const submitting = useRef(false);
  const [type, setType] = useState<FeedbackType>("bug");
  const [content, setContent] = useState("");
  const [contact, setContact] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const inputClass = "mt-2 w-full rounded-xl border border-slate-300 bg-white/80 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 dark:border-slate-600 dark:bg-slate-950/50 dark:text-slate-100 dark:placeholder:text-slate-400";

  function open() {
    setSuccess(false);
    setError("");
    dialog.current?.showModal();
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    if (content.trim().length < 5) {
      setError("请至少填写 5 个字，方便我们了解你的反馈。");
      return;
    }
    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      await submitFeedback({ type, content: content.trim(), contact: contact.trim() });
      setContent("");
      setContact("");
      setType("bug");
      setSuccess(true);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 429
        ? "提交太频繁，请等待一分钟后再试。你的内容已保留。"
        : "暂时未能提交，请稍后重试。你的内容已保留。");
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" onClick={open} aria-haspopup="dialog" aria-controls="site-feedback"
        className="fixed left-0 top-1/2 z-40 flex -translate-y-1/2 flex-col items-center gap-1 rounded-r-2xl border border-l-0 border-white/40 bg-white/85 px-2 py-3 text-xs font-medium text-slate-700 backdrop-blur-md transition-colors hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 dark:border-slate-600/70 dark:bg-slate-800/90 dark:text-slate-200 dark:hover:bg-slate-700 sm:px-3">
        <MessageSquarePlus size={18} aria-hidden="true" />
        <span>反馈</span>
      </button>
      <dialog ref={dialog} id="site-feedback" aria-labelledby="feedback-title" aria-describedby="feedback-description"
        onCancel={event => { if (busy) event.preventDefault(); }}
        className="fixed inset-0 m-auto mb-0 max-h-[90dvh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-white/95 p-5 text-slate-900 shadow-2xl backdrop:bg-slate-950/50 backdrop:backdrop-blur-sm dark:bg-slate-900/95 dark:text-slate-100 sm:mb-auto sm:w-[calc(100%-2rem)] sm:rounded-3xl sm:p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="feedback-title" className="text-xl font-bold">网站反馈</h2>
            <p id="feedback-description" className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">遇到问题，或有新的想法？欢迎告诉我。<br />无需登录，内容仅站长可见。</p>
          </div>
          <button type="button" disabled={busy} onClick={() => dialog.current?.close()} aria-label="关闭反馈"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 disabled:opacity-50 dark:hover:bg-slate-800"><X size={20} /></button>
        </div>
        {success ? (
          <div className="py-8 text-center" role="status">
            <CheckCircle2 className="mx-auto mb-4 text-sky-600 dark:text-sky-400" size={36} />
            <h3 className="text-lg font-semibold">反馈已收到</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">谢谢你帮助小站变得更好。</p>
            <button type="button" onClick={() => dialog.current?.close()} className="mt-6 rounded-xl bg-sky-700 px-6 py-3 text-sm font-medium text-white hover:bg-sky-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2">完成</button>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-6 space-y-5">
            <fieldset disabled={busy} className="space-y-5 disabled:opacity-70">
              <label className="block text-sm font-medium">反馈类型
                <select value={type} onChange={event => setType(event.target.value as FeedbackType)} className={inputClass}>
                  <option value="bug">问题反馈</option><option value="suggestion">功能建议</option><option value="other">其他</option>
                </select>
              </label>
              <label className="block text-sm font-medium">反馈内容 <span className="text-slate-500 dark:text-slate-400">（必填）</span>
                <textarea required minLength={5} maxLength={2000} rows={5} value={content} onChange={event => setContent(event.target.value)} placeholder="请描述遇到的问题，或你希望增加的功能…" className={`${inputClass} min-h-32 resize-y`} aria-describedby="feedback-count feedback-error" />
                <span id="feedback-count" className="mt-1 block text-right text-xs font-normal tabular-nums text-slate-500 dark:text-slate-400">{content.length} / 2000</span>
              </label>
              <label className="block text-sm font-medium">联系方式 <span className="text-slate-500 dark:text-slate-400">（选填）</span>
                <input type="text" maxLength={200} value={contact} onChange={event => setContact(event.target.value)} placeholder="邮箱或其他联系方式，方便联系你" className={inputClass} />
              </label>
            </fieldset>
            <p id="feedback-error" role="alert" className="text-sm text-red-700 dark:text-red-300">{error}</p>
            <button type="submit" disabled={busy} className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-sky-700 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-sky-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 disabled:cursor-wait disabled:opacity-60">
              {busy ? <Loader2 size={17} className="animate-spin" /> : <Send size={17} />} {busy ? "正在提交…" : "提交反馈"}
            </button>
          </form>
        )}
      </dialog>
    </>
  );
}
