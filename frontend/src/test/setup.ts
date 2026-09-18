import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock localStorage for jsdom and Node 26+ environment
const createLocalStorageMock = () => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString()
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    key: vi.fn((idx: number) => Object.keys(store)[idx] || null),
    get length() {
      return Object.keys(store).length
    },
  }
}

const mockStorage = createLocalStorageMock()
Object.defineProperty(window, 'localStorage', {
  value: mockStorage,
  writable: true,
})
try {
  Object.defineProperty(globalThis, 'localStorage', {
    value: mockStorage,
    writable: true,
  })
} catch {
  // Ignore if defined as getter in some runtimes
}

// Mock matchMedia for jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
