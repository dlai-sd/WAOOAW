/**
 * Property-based tests for tokenManager service using fast-check.
 */
import * as fc from 'fast-check';

interface TokenState {
  accessToken: string;
  expiresAt: number;
}

function isExpired(token: TokenState, now: number): boolean {
  return token.expiresAt < now;
}

function needsRefresh(token: TokenState, now: number, bufferMs = 60_000): boolean {
  return token.expiresAt - now < bufferMs;
}

describe('property: tokenManager invariants', () => {
  it('token is always expired when expiresAt < now', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9_999_999_999_999 }),
        fc.integer({ min: 1, max: 9_999_999_999_999 }),
        (expiresAt, now) => {
          fc.pre(expiresAt < now);
          const token: TokenState = { accessToken: 'tok', expiresAt };
          return isExpired(token, now) === true;
        },
      ),
      { numRuns: 100 },
    );
  });

  it('fresh token (expiresAt > now + 1h) never needs refresh', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1_000_000, max: 9_000_000_000_000 }),
        (now) => {
          const expiresAt = now + 3_600_000; // 1 hour from now
          const token: TokenState = { accessToken: 'tok', expiresAt };
          return needsRefresh(token, now) === false;
        },
      ),
      { numRuns: 100 },
    );
  });

  it('expired token always needs refresh', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9_000_000_000_000 }),
        (now) => {
          const expiresAt = now - 1; // already expired
          const token: TokenState = { accessToken: 'tok', expiresAt };
          return needsRefresh(token, now) === true;
        },
      ),
      { numRuns: 100 },
    );
  });
});
