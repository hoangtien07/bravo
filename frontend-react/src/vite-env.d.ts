/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Prefill đăng nhập cho build DEMO, dạng "email:password". Không đặt ở production. */
  readonly VITE_DEMO_LOGIN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
