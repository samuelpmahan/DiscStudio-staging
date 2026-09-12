import '../public/tick-part-checklist.js';
/** Small extension of neat's actual review-handoff overlay; inspection is not acceptance. */
const Base = customElements.get('tick-part-checklist');
export class NeatReview extends Base {
  save() {
    try { localStorage.setItem(`tick-part-checklist:${this.key}`, JSON.stringify(this.s)); }
    catch { this.shadowRoot.querySelector('#storage-warning')?.remove(); const p = document.createElement('p'); p.id = 'storage-warning'; p.textContent = 'Browser storage is full. Export this review to preserve it.'; this.shadowRoot.querySelector('section')?.append(p); }
  }
  draw() {
    super.draw();
    this.s.comments ??= {}; this.s.contexts ??= {};
    const open = this.shadowRoot.querySelector('#open'); if (open) open.textContent = '☑ Review & comments';
    const section = this.shadowRoot.querySelector('section');
    const intro = document.createElement('p'); intro.className = 'intro'; intro.textContent = 'Check what you inspected. Leave a comment on the exact item. Saved here; export to hand back. This does not accept or promote code.';
    section?.querySelector('header')?.after(intro);
    for (const tick of this.k) for (const part of tick.parts ?? []) {
      const check = [...this.shadowRoot.querySelectorAll('[data-p]')].find(e => e.dataset.t === tick.id && e.dataset.p === part.id);
      if (!check) continue;
      const li = check.closest('li'), textarea = document.createElement('textarea');
      const key = part.reviewId || `${tick.id}.${part.id}`;
      textarea.placeholder = 'What should change?'; textarea.setAttribute('aria-label', `Comment: ${part.label}`); textarea.dataset.reviewId = key; textarea.rows = 2;
      textarea.value = this.s.comments[key] || '';
      textarea.addEventListener('input', () => { this.s.comments[key] = textarea.value; this.s.contexts[key] = this.getContext?.() ?? {}; this.save(); });
      li.append(textarea);
      if (part.verification) { const note = document.createElement('small'); note.textContent = part.verification; li.append(note); }
      li.querySelector('a')?.removeAttribute('target');
    }
    const name = document.createElement('input'); name.type = 'text'; name.placeholder = 'Your name (for the exported review)'; name.setAttribute('aria-label', 'Reviewer name'); name.value = this.s.human || '';
    name.addEventListener('input', () => { this.s.human = name.value; this.save(); });
    section?.querySelector('#export')?.before(name);
  }
  export(checks) {
    if (!this.s.human?.trim()) { this.shadowRoot.querySelector('[aria-label="Reviewer name"]')?.focus(); return; }
    const data = { schemaVersion: 1, id: `inspection-${Date.now()}`, submissionId: this.getAttribute('submission-id'), itemId: this.getAttribute('item-id'), checkpointId: this.getAttribute('checkpoint-id'), subjectCommit: this.getAttribute('subject-commit'), human: this.s.human.trim(), inspected: Object.fromEntries(checks.map(p => [p.reviewId, !!this.s.parts[p._tick]?.[p.id]])), comments: this.s.comments, contexts: this.s.contexts, recordedAt: new Date().toISOString(), acceptance: 'not-recorded' };
    this.dispatchEvent(new CustomEvent('neat:inspection-export', { detail: data, bubbles: true }));
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })); a.download = `${data.id}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  css() { return super.css() + ':host{width:min(420px,calc(100vw - 24px));color:#203d36}.w{border-color:#bcc8af;border-radius:12px;background:#fbfaf6;box-shadow:0 8px 30px #203d3626}section{max-height:min(720px,calc(100vh - 100px))}header{position:sticky;top:0;background:#fbfaf6;z-index:1}.intro{font-size:12px;color:#5f7267;padding:0 16px}textarea{display:block;box-sizing:border-box;width:100%;padding:8px;margin:7px 0 3px;resize:vertical;border:1px solid #ccd5c2;border-radius:6px;background:#fff;font:13px system-ui;color:#203d36}li li{border-top:1px solid #e3e7db;padding:9px 0}li small{padding:4px 0;color:#627459;font-size:11px}a{color:#426129}button{padding:8px 12px;border:1px solid #c5cebb;border-radius:6px;background:#e8eedf;color:#203d36;cursor:pointer}section>input{box-sizing:border-box;display:block;width:calc(100% - 24px);padding:9px;margin:12px;border:1px solid #c5cebb;border-radius:6px}input[type=checkbox]{accent-color:#56733a}ul ul{padding-left:12px}#open{font-weight:600}#storage-warning{color:#a02e2e;padding:10px}'; }
}
customElements.define('neat-review', NeatReview);
export { reviewItems } from './review-data.js';
