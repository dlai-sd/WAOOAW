/**
 * Firebase Analytics Service
 * Tracks user behavior, conversion funnels, and key business metrics
 */

// import analytics from '@react-native-firebase/analytics'; // REMOVED for demo build
const analytics = (): any => ({
  logEvent: async (_name?: string, _params?: Record<string, any>) => {},
  logScreenView: async (_params?: Record<string, any>) => {},
  setUserId: async (_userId?: string) => {},
  setUserProperty: async (_name?: string, _value?: string) => {},
  setAnalyticsCollectionEnabled: async (_enabled?: boolean) => {},
  logLogin: async (_params?: Record<string, any>) => {},
  logSignUp: async (_params?: Record<string, any>) => {},
  logViewItem: async (_params?: Record<string, any>) => {},
  logSearch: async (_params?: Record<string, any>) => {},
  logBeginCheckout: async (_params?: Record<string, any>) => {},
  logPurchase: async (_params?: Record<string, any>) => {},
});
import { config } from '../../config/environment.config';

export interface AnalyticsEvent {
  name: string;
  params?: Record<string, any>;
}

export class FirebaseAnalyticsService {
  private initialized = false;

  async setAnalyticsCollectionEnabled(enabled: boolean): Promise<void> {
    await analytics().setAnalyticsCollectionEnabled(enabled);
  }

  async logEvent(name: string, params?: Record<string, any>): Promise<void> {
    await analytics().logEvent(name, params);
  }

  /**
   * Initialize Firebase Analytics
   * Call this once in App.tsx on mount
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Disable in development mode
      if (!config.features.analytics) {
        await analytics().setAnalyticsCollectionEnabled(false);
        console.log('[Analytics] Disabled in development mode');
        return;
      }

      await analytics().setAnalyticsCollectionEnabled(true);
      this.initialized = true;
      console.log('[Analytics] Initialized successfully');
    } catch (error) {
      console.error('[Analytics] Initialization failed:', error);
    }
  }

  /**
   * Set user ID for tracking across sessions
   */
  async setUserId(userId: string): Promise<void> {
    try {
      await analytics().setUserId(userId);
    } catch (error) {
      console.error('[Analytics] Failed to set user ID:', error);
    }
  }

  /**
   * Set user properties for segmentation
   */
  async setUserProperty(name: string, value: string): Promise<void> {
    try {
      await analytics().setUserProperty(name, value);
    } catch (error) {
      console.error('[Analytics] Failed to set user property:', error);
    }
  }

  // ============================================================================
  // AUTHENTICATION EVENTS
  // ============================================================================

  async trackSignIn(method: 'google' | 'apple' | 'email'): Promise<void> {
    try {
      await analytics().logLogin({ method });
    } catch (error) {
      console.error('[Analytics] Failed to track sign in:', error);
    }
  }

  async trackSignUp(method: 'google' | 'apple' | 'email'): Promise<void> {
    try {
      await analytics().logSignUp({ method });
    } catch (error) {
      console.error('[Analytics] Failed to track sign up:', error);
    }
  }

  async trackSignOut(): Promise<void> {
    try {
      await analytics().logEvent('sign_out', {});
    } catch (error) {
      console.error('[Analytics] Failed to track sign out:', error);
    }
  }

  // ============================================================================
  // AGENT DISCOVERY EVENTS
  // ============================================================================

  async trackAgentView(agentId: string, agentName: string, industry: string): Promise<void> {
    try {
      await analytics().logViewItem({
        item_id: agentId,
        item_name: agentName,
        item_category: industry,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track agent view:', error);
    }
  }

  async trackAgentSearch(searchTerm: string, resultsCount: number): Promise<void> {
    try {
      await analytics().logSearch({
        search_term: searchTerm,
        results_count: resultsCount,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track agent search:', error);
    }
  }

  async trackAgentFilter(filterType: string, filterValue: string): Promise<void> {
    try {
      await analytics().logEvent('agent_filter', {
        filter_type: filterType,
        filter_value: filterValue,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track agent filter:', error);
    }
  }

  // ============================================================================
  // HIRE FLOW EVENTS (Conversion Funnel)
  // ============================================================================

  async trackHireStart(agentId: string, planType: 'monthly' | 'quarterly' | 'annual'): Promise<void> {
    try {
      await analytics().logBeginCheckout({
        item_id: agentId,
        value: 12000, // Default value in INR
        currency: 'INR',
        item_category: planType,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track hire start:', error);
    }
  }

  async trackHireStepComplete(step: string, agentId: string): Promise<void> {
    try {
      await analytics().logEvent('hire_step_complete', {
        step,
        agent_id: agentId,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track hire step:', error);
    }
  }

  async trackHireComplete(
    agentId: string,
    planType: string,
    amount: number,
    transactionId: string
  ): Promise<void> {
    try {
      await analytics().logPurchase({
        transaction_id: transactionId,
        value: amount,
        currency: 'INR',
        items: [
          {
            item_id: agentId,
            item_name: `Agent ${agentId}`,
            item_category: planType,
            price: amount,
            quantity: 1,
          },
        ],
      });
    } catch (error) {
      console.error('[Analytics] Failed to track hire complete:', error);
    }
  }

  async trackHireCancel(agentId: string, step: string): Promise<void> {
    try {
      await analytics().logEvent('hire_cancel', {
        agent_id: agentId,
        cancel_step: step,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track hire cancel:', error);
    }
  }

  // ============================================================================
  // TRIAL MANAGEMENT EVENTS
  // ============================================================================

  async trackTrialStart(agentId: string): Promise<void> {
    try {
      await analytics().logEvent('trial_start', { agent_id: agentId });
    } catch (error) {
      console.error('[Analytics] Failed to track trial start:', error);
    }
  }

  async trackTrialComplete(agentId: string, converted: boolean): Promise<void> {
    try {
      await analytics().logEvent('trial_complete', {
        agent_id: agentId,
        converted,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track trial complete:', error);
    }
  }

  async trackDeliverableView(deliverableId: string, type: string): Promise<void> {
    try {
      await analytics().logEvent('deliverable_view', {
        deliverable_id: deliverableId,
        type,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track deliverable view:', error);
    }
  }

  // ============================================================================
  // VOICE CONTROL EVENTS
  // ============================================================================

  async trackVoiceCommand(command: string, success: boolean): Promise<void> {
    try {
      await analytics().logEvent('voice_command', {
        command,
        success,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track voice command:', error);
    }
  }

  // ============================================================================
  // SCREEN TRACKING
  // ============================================================================

  async trackScreen(screenName: string, screenClass: string): Promise<void> {
    try {
      await analytics().logScreenView({
        screen_name: screenName,
        screen_class: screenClass,
      });
    } catch (error) {
      console.error('[Analytics] Failed to track screen:', error);
    }
  }

  // ============================================================================
  // CUSTOM EVENTS
  // ============================================================================

  async trackEvent(event: AnalyticsEvent): Promise<void> {
    try {
      await analytics().logEvent(event.name, event.params || {});
    } catch (error) {
      console.error(`[Analytics] Failed to track event ${event.name}:`, error);
    }
  }
}

// Export singleton instance
export const analyticsService = new FirebaseAnalyticsService();
