export interface SyncRequest {
  id: string; // usually a UUID or timestamp-based ID
  url: string;
  method: string;
  headers: Record<string, string>;
  body: unknown;
  created_at: string;
  status: 'PENDING' | 'CONFLICTED' | 'FAILED';
  error?: string;
}

const DB_NAME = 'dwrms_offline_db';
const DB_VERSION = 1;
const STORE_SYNC_QUEUE = 'sync_queue';
const STORE_DRAFTS = 'drafts';

class OfflineStore {
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    if (this.db) return;
    if (typeof window === 'undefined') return;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        if (!db.objectStoreNames.contains(STORE_SYNC_QUEUE)) {
          db.createObjectStore(STORE_SYNC_QUEUE, { keyPath: 'id' });
        }
        
        if (!db.objectStoreNames.contains(STORE_DRAFTS)) {
          db.createObjectStore(STORE_DRAFTS, { keyPath: 'id' });
        }
      };

      request.onsuccess = (event: Event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve();
      };

      request.onerror = (event: Event) => {
        reject((event.target as IDBOpenDBRequest).error);
      };
    });
  }

  // --- Sync Queue Methods ---

  async addSyncRequest(req: SyncRequest): Promise<void> {
    await this.init();
    return new Promise((resolve, reject) => {
      if (!this.db) return reject('DB not initialized');
      const transaction = this.db.transaction([STORE_SYNC_QUEUE], 'readwrite');
      const store = transaction.objectStore(STORE_SYNC_QUEUE);
      const request = store.put(req);

      request.onsuccess = () => resolve();
      request.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  async getSyncRequests(): Promise<SyncRequest[]> {
    await this.init();
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve([]);
      const transaction = this.db.transaction([STORE_SYNC_QUEUE], 'readonly');
      const store = transaction.objectStore(STORE_SYNC_QUEUE);
      const request = store.getAll();

      request.onsuccess = (e) => resolve((e.target as IDBRequest).result);
      request.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  async updateSyncRequest(req: SyncRequest): Promise<void> {
    return this.addSyncRequest(req); // PUT overwrites
  }

  async deleteSyncRequest(id: string): Promise<void> {
    await this.init();
    return new Promise((resolve, reject) => {
      if (!this.db) return reject('DB not initialized');
      const transaction = this.db.transaction([STORE_SYNC_QUEUE], 'readwrite');
      const store = transaction.objectStore(STORE_SYNC_QUEUE);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  // --- Drafts Methods ---

  async saveDraft<T = unknown>(id: string, data: T): Promise<void> {
    await this.init();
    return new Promise((resolve, reject) => {
      if (!this.db) return reject('DB not initialized');
      const transaction = this.db.transaction([STORE_DRAFTS], 'readwrite');
      const store = transaction.objectStore(STORE_DRAFTS);
      const request = store.put({ id, data, updated_at: new Date().toISOString() });

      request.onsuccess = () => resolve();
      request.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  async getDraft<T = unknown>(id: string): Promise<T | null> {
    await this.init();
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve(null);
      const transaction = this.db.transaction([STORE_DRAFTS], 'readonly');
      const store = transaction.objectStore(STORE_DRAFTS);
      const request = store.get(id);

      request.onsuccess = (e) => {
        const result = (e.target as IDBRequest).result;
        resolve(result ? result.data : null);
      };
      request.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  async deleteDraft(id: string): Promise<void> {
    await this.init();
    return new Promise((resolve, reject) => {
      if (!this.db) return reject('DB not initialized');
      const transaction = this.db.transaction([STORE_DRAFTS], 'readwrite');
      const store = transaction.objectStore(STORE_DRAFTS);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }
}

export const offlineStore = new OfflineStore();
