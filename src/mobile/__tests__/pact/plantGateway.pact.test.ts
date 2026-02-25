/**
 * Mobile consumer Pact definitions for Plant Gateway.
 *
 * Defines contract interactions the mobile app expects from Plant Gateway.
 * Pact JSON files are written to tests/contracts/pacts/.
 */

import path from 'path';
import { Pact, Matchers } from '@pact-foundation/pact';

const { like, string } = Matchers;

const PACT_DIR = path.resolve(__dirname, '../../../../tests/contracts/pacts');

const provider = new Pact({
  consumer: 'mobile-app',
  provider: 'plant-gateway',
  port: 1235,
  log: path.resolve(__dirname, 'logs', 'pact.log'),
  dir: PACT_DIR,
  logLevel: 'warn',
});

beforeAll(() => provider.setup());
afterEach(() => provider.verify());
afterAll(() => provider.finalize());

describe('Plant Gateway Pact — Mobile Consumer', () => {

  describe('POST /auth/otp/start', () => {
    beforeEach(() =>
      provider.addInteraction({
        state: 'a phone number is available',
        uponReceiving: 'a request to start OTP',
        withRequest: {
          method: 'POST',
          path: '/auth/otp/start',
          headers: { 'Content-Type': 'application/json' },
          body: { phone: '+919876543210' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: like({ message: 'OTP sent', otp_id: string('otp-mock-001') }),
        },
      })
    );

    it('returns 200 with otp_id', async () => {
      const res = await fetch(`http://localhost:1235/auth/otp/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: '+919876543210' }),
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.otp_id).toBeDefined();
    });
  });

  describe('POST /auth/otp/verify', () => {
    beforeEach(() =>
      provider.addInteraction({
        state: 'a valid OTP exists',
        uponReceiving: 'a request to verify OTP',
        withRequest: {
          method: 'POST',
          path: '/auth/otp/verify',
          headers: { 'Content-Type': 'application/json' },
          body: { phone: '+919876543210', otp: '123456', otp_id: 'otp-mock-001' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: like({
            access_token: string('mock-access-token'),
            refresh_token: string('mock-refresh-token'),
            token_type: 'bearer',
          }),
        },
      })
    );

    it('returns 200 with tokens', async () => {
      const res = await fetch(`http://localhost:1235/auth/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: '+919876543210', otp: '123456', otp_id: 'otp-mock-001' }),
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.access_token).toBeDefined();
    });
  });

  describe('GET /agents', () => {
    beforeEach(() =>
      provider.addInteraction({
        state: 'agents are available',
        uponReceiving: 'a request to list agents',
        withRequest: {
          method: 'GET',
          path: '/agents',
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: like([
            like({ id: string('agent-001'), name: string('Marketing Expert'), status: string('available') }),
          ]),
        },
      })
    );

    it('returns 200 with agent list', async () => {
      const res = await fetch(`http://localhost:1235/agents`);
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(Array.isArray(body)).toBe(true);
    });
  });

  describe('POST /hire/:id/confirm', () => {
    beforeEach(() =>
      provider.addInteraction({
        state: 'a hire draft hire-mock-001 exists',
        uponReceiving: 'a request to confirm hire hire-mock-001',
        withRequest: {
          method: 'POST',
          path: '/hire/hire-mock-001/confirm',
          headers: { 'Content-Type': 'application/json' },
          body: {},
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: like({ hire_id: string('hire-mock-001'), status: string('confirmed') }),
        },
      })
    );

    it('returns 200 with confirmed hire', async () => {
      const res = await fetch(`http://localhost:1235/hire/hire-mock-001/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.status).toBe('confirmed');
    });
  });
});
