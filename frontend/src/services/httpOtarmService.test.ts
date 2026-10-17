import { beforeEach, describe, expect, it, vi } from 'vitest';
import { HttpOtarmService } from './httpOtarmService';

function memoryStorage() {
  const values = new Map<string,string>();
  return {
    getItem: (key:string) => values.get(key) ?? null,
    setItem: (key:string,value:string) => values.set(key,value),
    removeItem: (key:string) => values.delete(key),
  };
}

describe('HttpOtarmService', () => {
  const storage = memoryStorage();
  beforeEach(() => storage.removeItem('otarm.session'));

  it('authenticates and adds the bearer token to backend requests', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ accessToken:'signed-token', tokenType:'bearer', expiresIn:3600, user:{ id:'u1', email:'admin@otarm.demo', displayName:'Admin User', role:'ADMIN' } }), { status:200, headers:{ 'Content-Type':'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id:'site-1', code:'ONE', name:'Test Site' }]), { status:200, headers:{ 'Content-Type':'application/json' } }));
    const service = new HttpOtarmService('http://backend/api/v1', fetcher, storage);

    await service.login({ email:'admin@otarm.demo', password:'demo-password' });
    await service.getSites();

    expect(fetcher).toHaveBeenNthCalledWith(1, 'http://backend/api/v1/auth/token', expect.objectContaining({ method:'POST' }));
    const secondInit = fetcher.mock.calls[1][1] as RequestInit;
    expect(new Headers(secondInit.headers).get('Authorization')).toBe('Bearer signed-token');
  });

  it('encodes filters and returns CSV text', async () => {
    storage.setItem('otarm.session', JSON.stringify({ accessToken:'token', expiresAt:Date.now()+60_000, user:{ id:'u1', email:'admin@otarm.demo', displayName:'Admin User', role:'ADMIN' } }));
    const fetcher = vi.fn().mockResolvedValue(new Response('Asset tag,Name\nA-1,PLC', { status:200 }));
    const service = new HttpOtarmService('/api/v1', fetcher, storage);

    await expect(service.exportAssetsCsv({ search:'boiler room', siteId:'site-1' })).resolves.toContain('A-1');
    expect(fetcher.mock.calls[0][0]).toBe('/api/v1/assets/export.csv?search=boiler+room&siteId=site-1');
  });

  it('clears an invalid session after a 401 response', async () => {
    storage.setItem('otarm.session', JSON.stringify({ accessToken:'expired', expiresAt:Date.now()+60_000, user:{ id:'u1', email:'admin@otarm.demo', displayName:'Admin User', role:'ADMIN' } }));
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ code:'UNAUTHENTICATED', message:'Session expired.' }), { status:401, headers:{ 'Content-Type':'application/json' } }));
    const service = new HttpOtarmService('/api/v1', fetcher, storage);

    await expect(service.getSites()).rejects.toMatchObject({ code:'UNAUTHENTICATED' });
    expect(service.getSession()).toBeNull();
  });

  it('invokes fetch without binding it to the service instance', async () => {
    storage.setItem('otarm.session', JSON.stringify({ accessToken:'token', expiresAt:Date.now()+60_000, user:{ id:'u1', email:'admin@otarm.demo', displayName:'Admin User', role:'ADMIN' } }));
    const fetcher = vi.fn(function(this: unknown) {
      if (this instanceof HttpOtarmService) throw new TypeError('Illegal invocation');
      return Promise.resolve(new Response('[]', { status:200, headers:{ 'Content-Type':'application/json' } }));
    });
    const service = new HttpOtarmService('/api/v1', fetcher, storage);

    await expect(service.getSites()).resolves.toEqual([]);
  });
});
