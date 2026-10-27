// Encrypted on-device store for the inspector app (NFR-16).
// Everything (sign-in token, assigned cases, queued outcomes, photos) is encrypted with AES-GCM
// under a non-extractable WebCrypto key kept in IndexedDB: the raw key can never be read out
// by scripts or copied off the device. Photos stay inside the app (never the camera roll).
// Data is wiped after sync, within 24 hours, and on remote sign-out.

const DB_NAME = "voltguard-field";
const STORE = "kv";
export const MAX_AGE_MS = 24 * 60 * 60 * 1000;

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function tx(db, mode, fn) {
  return new Promise((resolve, reject) => {
    const t = db.transaction(STORE, mode);
    const store = t.objectStore(STORE);
    const result = fn(store);
    t.oncomplete = () => resolve(result?.result);
    t.onerror = () => reject(t.error);
  });
}

async function rawGet(key) {
  const db = await openDb();
  try {
    return await tx(db, "readonly", (s) => s.get(key));
  } finally {
    db.close();
  }
}

async function rawPut(key, value) {
  const db = await openDb();
  try {
    await tx(db, "readwrite", (s) => s.put(value, key));
  } finally {
    db.close();
  }
}

async function rawDelete(key) {
  const db = await openDb();
  try {
    await tx(db, "readwrite", (s) => s.delete(key));
  } finally {
    db.close();
  }
}

let keyPromise = null;
async function cryptoKey() {
  if (!keyPromise) {
    keyPromise = (async () => {
      let key = await rawGet("__key");
      if (!key) {
        key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
        await rawPut("__key", key);
      }
      return key;
    })();
  }
  return keyPromise;
}

export async function put(name, value) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plain = value instanceof ArrayBuffer ? value : new TextEncoder().encode(JSON.stringify(value));
  const data = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await cryptoKey(), plain);
  await rawPut(name, { iv, data, binary: value instanceof ArrayBuffer, savedAt: Date.now() });
}

export async function get(name) {
  const box = await rawGet(name);
  if (!box) return null;
  const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: box.iv }, await cryptoKey(), box.data);
  return box.binary ? plain : JSON.parse(new TextDecoder().decode(plain));
}

export const remove = rawDelete;

export async function keys() {
  const db = await openDb();
  try {
    return await tx(db, "readonly", (s) => s.getAllKeys());
  } finally {
    db.close();
  }
}

// Remove everything, including the key itself (remote sign-out, 24-hour limit, manual wipe).
export async function wipeAll() {
  keyPromise = null;
  await new Promise((resolve) => {
    const req = indexedDB.deleteDatabase(DB_NAME);
    req.onsuccess = req.onerror = req.onblocked = () => resolve();
  });
}

// Wipe when the cached cases are older than 24 hours.
export async function enforceMaxAge(now = Date.now()) {
  const meta = await get("meta").catch(() => null);
  if (meta?.downloadedAt && now - meta.downloadedAt > MAX_AGE_MS) {
    await wipeAll();
    return true;
  }
  return false;
}
