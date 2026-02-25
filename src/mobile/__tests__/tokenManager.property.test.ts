/**
 * Property-based tests for TokenManagerService invariants.
 *
 * Invariants under test:
 *   1. A token is expired if expiresAt (exp) < current time.
 *   2. shouldRefreshToken returns false for tokens with plenty of time remaining.
 *   3. shouldRefreshToken returns true only when token is within the threshold window.
 */

import * as fc from 'fast-check';
import TokenManagerService, {
  type DecodedToken,
} from '../../src/services/tokenManager.service';

const nowSeconds = () => Math.floor(Date.now() / 1000);

/** Build a minimal DecodedToken for property tests. */
function makeToken(overrides: Partial<DecodedToken> = {}): DecodedToken {
  const now = nowSeconds();
  return {
    user_id: 'user-prop-test',
    email: 'prop@waooaw.com',
    token_type: 'access',
    exp: now + 900, // 15 minutes by default
    iat: now,
    roles: ['user'],
    iss: 'waooaw.com',
    sub: 'user-prop-test',
    ...overrides,
  };
}

describe('property', () => {
  describe('TokenManagerService invariants', () => {

    it('token is expired when exp is in the past', () => {
      const now = nowSeconds();

      fc.assert(
        fc.property(
          fc.integer({ min: 1, max: 86400 }), // 1 second to 24 hours in the past
          (secondsAgo) => {
            const token = makeToken({ exp: now - secondsAgo });
            const timeUntilExpiry = TokenManagerService.getTimeUntilExpiry(token);
            return timeUntilExpiry <= 0;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('token is not expired when exp is in the future', () => {
      const now = nowSeconds();

      fc.assert(
        fc.property(
          fc.integer({ min: 120, max: 86400 }), // 2 minutes to 24 hours in the future
          (secondsAhead) => {
            const token = makeToken({ exp: now + secondsAhead });
            const timeUntilExpiry = TokenManagerService.getTimeUntilExpiry(token);
            return timeUntilExpiry > 0;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('shouldRefreshToken returns false for tokens with plenty of time remaining', () => {
      const now = nowSeconds();
      const threshold = 60; // default threshold

      fc.assert(
        fc.property(
          fc.integer({ min: threshold + 10, max: 86400 }), // well beyond threshold
          (secondsAhead) => {
            const token = makeToken({ exp: now + secondsAhead });
            // Token has more time than threshold — should NOT trigger refresh
            return TokenManagerService.shouldRefreshToken(token, threshold) === false;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('shouldRefreshToken returns true when token is within the refresh threshold', () => {
      const now = nowSeconds();
      const threshold = 60;

      fc.assert(
        fc.property(
          fc.integer({ min: 1, max: threshold - 1 }), // inside threshold window
          (secondsAhead) => {
            const token = makeToken({ exp: now + secondsAhead });
            return TokenManagerService.shouldRefreshToken(token, threshold) === true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('getTimeUntilExpiry is deterministic for the same token', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: -3600, max: 86400 }),
          (exp) => {
            const now = nowSeconds();
            const token = makeToken({ exp: now + exp });
            const t1 = TokenManagerService.getTimeUntilExpiry(token);
            const t2 = TokenManagerService.getTimeUntilExpiry(token);
            // Values may differ by at most 1 second due to clock tick
            return Math.abs(t1 - t2) <= 1;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
