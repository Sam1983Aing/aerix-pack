// ThreeUI polish: the model arrives in stages instead of one 138 MB file.
// manifest.json describes a light "hero" GLB (everything you see in the first frames,
// with small placeholder textures) and a "details" stage holding the deferred interior
// geometry. Full-size textures are separate webp files, upgraded chapter by chapter.
let manifestPromise;
export function readManifest(url) {
  return manifestPromise ||= fetch(url).then((response) => {
    if (!response.ok) throw new Error(`Model manifest: HTTP ${response.status}`);
    return response.json();
  });
}

// Download one stage's segments in parallel (up to 3) and reassemble its exact bytes.
export async function loadModelData(manifestURL, onProgress = () => {}, stage = "hero", signal) {
  const controller = new AbortController();
  signal?.addEventListener("abort", () => controller.abort(), { once: true });
  if (signal?.aborted) controller.abort();
  const manifest = await readManifest(manifestURL);
  const part = stage === "hero" ? manifest : manifest[stage];
  if (!part || !Number.isSafeInteger(part.bytes) || part.bytes <= 0 || !Array.isArray(part.parts)) {
    throw new Error("Invalid model manifest");
  }
  const data = new Uint8Array(part.bytes);
  let next = 0, received = 0;
  const report = (amount) => { received += amount; onProgress(received / part.bytes); };
  async function worker() {
    while (next < part.parts.length) {
      const segment = part.parts[next++];
      if (!Number.isSafeInteger(segment.offset) || !Number.isSafeInteger(segment.bytes) || segment.offset < 0 || segment.offset + segment.bytes > data.length) {
        throw new Error("Invalid model segment");
      }
      const result = await fetch(new URL(segment.file, manifestURL), { signal: controller.signal });
      if (!result.ok) throw new Error(`Model segment: HTTP ${result.status}`);
      let length = 0;
      const accept = (chunk) => {
        if (length + chunk.length > segment.bytes) throw new Error("Oversized model segment");
        data.set(chunk, segment.offset + length);
        length += chunk.length;
        report(chunk.length);
      };
      if (result.body) {
        const reader = result.body.getReader();
        try {
          while (true) {
            const chunk = await reader.read();
            if (chunk.done) break;
            accept(chunk.value);
          }
        } finally { reader.releaseLock(); }
      } else {
        accept(new Uint8Array(await result.arrayBuffer()));
      }
      if (length !== segment.bytes) throw new Error("Incomplete model segment");
    }
  }
  try {
    await Promise.all(Array.from({ length: Math.min(3, part.parts.length) }, worker));
    if (received !== part.bytes) throw new Error("Incomplete model");
    return data.buffer;
  } catch (error) {
    controller.abort();
    throw error;
  }
}
