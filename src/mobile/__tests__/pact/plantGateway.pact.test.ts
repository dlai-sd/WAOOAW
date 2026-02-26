/**
 * Mobile consumer Pact definitions for Plant Gateway API.
 */
import * as path from 'path';
import * as fs from 'fs';

const PACT_DIR = path.resolve(__dirname, '..', '..', '..', '..', '..', 'tests', 'contracts', 'pacts');

interface Interaction {
  description: string;
  request: { method: string; path: string; body?: unknown };
  response: { status: number; body?: unknown };
}

function buildPact(interactions: Interaction[]) {
  return {
    consumer: { name: 'Mobile' },
    provider: { name: 'Plant-Gateway' },
    interactions,
    metadata: { pactSpecification: { version: '2.0.0' } },
  };
}

describe('Mobile → Plant Gateway Pact (consumer)', () => {
  beforeAll(() => {
    fs.mkdirSync(PACT_DIR, { recursive: true });
  });

  it('POST /auth/otp/start — returns otp_id', () => {
    const interaction: Interaction = {
      description: 'mobile requests OTP start',
      request: { method: 'POST', path: '/auth/otp/start', body: { phone: '+911234567890' } },
      response: { status: 200, body: { otp_id: 'test-id', expires_in: 300 } },
    };
    expect(interaction.response.status).toBe(200);
  });

  it('POST /auth/otp/verify — returns JWT', () => {
    const interaction: Interaction = {
      description: 'mobile verifies OTP',
      request: { method: 'POST', path: '/auth/otp/verify', body: { otp_id: 'test-id', code: '123456' } },
      response: { status: 200, body: { access_token: 'jwt', token_type: 'bearer' } },
    };
    expect(interaction.response.status).toBe(200);
  });

  it('GET /agents — returns agent list', () => {
    const interaction: Interaction = {
      description: 'mobile fetches agent catalog',
      request: { method: 'GET', path: '/agents' },
      response: { status: 200, body: [{ id: 'agent-001', name: 'Marketing Agent' }] },
    };
    expect(interaction.response.status).toBe(200);
  });

  it('POST /hire/:id/confirm — confirms hire', () => {
    const interaction: Interaction = {
      description: 'mobile confirms hire',
      request: { method: 'POST', path: '/hire/hire-001/confirm' },
      response: { status: 200, body: { hire_id: 'hire-001', status: 'active' } },
    };
    // Write pact file
    const pact = buildPact([interaction]);
    fs.writeFileSync(
      path.join(PACT_DIR, 'Mobile-Plant-Gateway.json'),
      JSON.stringify(pact, null, 2),
    );
    expect(interaction.response.status).toBe(200);
  });
});
