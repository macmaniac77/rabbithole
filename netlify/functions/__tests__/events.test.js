import { describe, it, expect, beforeAll } from 'vitest';
import events from '../events.js';

describe('events function', () => {
    beforeAll(() => {
        global.fetch = async () => ({ ok: true });
    });

    it('returns 200 for valid payload', async () => {
        const req = new Request('http://localhost/api/events', {
            method: 'POST',
            body: JSON.stringify({ event: 'test', page: '/test' }),
            headers: { 'Content-Type': 'application/json' }
        });
        const res = await events(req);
        expect(res.status).toBe(200);
    });
});
