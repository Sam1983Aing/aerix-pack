// ThreeUI polish: one loader at a time, most urgent first.
// Everything after the hero frame (interior geometry, full textures, the five worlds)
// goes through this queue, so downloads and GPU uploads never pile up on the scroll.
// Each job waits two animation frames before it starts, keeping scrolling smooth.
// A lower priority number runs sooner. A failed job can be retried once after a second.
export function createAssetQueue({
  yieldTask = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))),
  onChange = () => {},
} = {}) {
  const jobs = new Map(), controller = new AbortController();
  let active = false, disposed = false;
  const report = () => onChange([...jobs.values()].map(({ key, state, attempts }) => ({ key, state, attempts })));
  async function pump() {
    if (active || disposed) return;
    const job = [...jobs.values()].filter((j) => j.state === "queued").sort((a, b) => a.priority - b.priority)[0];
    if (!job) return;
    active = true;
    job.state = "loading";
    report();
    try {
      await yieldTask();
      if (disposed) throw new Error("Asset queue disposed");
      await job.load(controller.signal);
      if (disposed) throw new Error("Asset queue disposed");
      job.state = "ready";
      job.resolve();
    } catch (error) {
      job.state = "error";
      job.failedAt = Date.now();
      job.reject(error);
    } finally {
      active = false;
      report();
      queueMicrotask(pump);
    }
  }
  return {
    request(key, load, priority = 10, retry = false) {
      let job = jobs.get(key);
      if (job && !(retry && job.state === "error" && job.attempts < 2 && Date.now() - job.failedAt >= 1000)) {
        job.priority = Math.min(job.priority, priority);
        return job.promise;
      }
      if (disposed) return Promise.resolve();
      const attempts = (job?.attempts || 0) + 1;
      job = { key, load, priority, attempts, state: "queued" };
      job.promise = new Promise((resolve, reject) => Object.assign(job, { resolve, reject }));
      job.promise.catch(() => {});
      jobs.set(key, job);
      report();
      queueMicrotask(pump);
      return job.promise;
    },
    state: (key) => jobs.get(key)?.state || "idle",
    dispose() {
      disposed = true;
      controller.abort();
      for (const job of jobs.values()) if (job.state === "queued") {
        job.state = "error";
        job.reject(new Error("Asset queue disposed"));
      }
      report();
    },
  };
}
