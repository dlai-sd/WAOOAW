/**
 * User Data Service
 * 
 * Manages persistent user data storage using AsyncStorage
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const USER_DATA_KEY = '@waooaw:userData';

export interface StoredUserData {
  customer_id: string;
  email: string;
  full_name?: string;
  phone?: string;
  business_name?: string;
}

class UserDataService {
  /**
   * Save user data to persistent storage
   */
  async saveUserData(userData: StoredUserData): Promise<void> {
    try {
      await AsyncStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
      console.log('[UserDataService] User data saved successfully');
    } catch (error) {
      console.error('[UserDataService] Error saving user data:', error);
      throw error;
    }
  }

  /**
   * Get user data from persistent storage
   */
  async getUserData(): Promise<StoredUserData | null> {
    try {
      const data = await AsyncStorage.getItem(USER_DATA_KEY);
      if (data) {
        console.log('[UserDataService] User data retrieved');
        return JSON.parse(data);
      }
      console.log('[UserDataService] No user')
;
      return null;
    } catch (error) {
      console.error('[UserDataService] Error retrieving user data:', error);
      return null;
    }
  }

  /**
   * Clear user data from persistent storage
   */
  async clearUserData(): Promise<void> {
    try {
      await AsyncStorage.removeItem(USER_DATA_KEY);
      console.log('[UserDataService] User data cleared');
    } catch (error) {
      console.error('[UserDataService] Error clearing user data:', error);
      throw error;
    }
  }

  /**
   * Update specific user fields
   */
  async updateUserData(updates: Partial<StoredUserData>): Promise<void> {
    try {
      const existingData = await this.getUserData();
      if (existingData) {
        const updatedData = { ...existingData, ...updates };
        await this.saveUserData(updatedData);
      }
    } catch (error) {
      console.error('[UserDataService] Error updating user data:', error);
      throw error;
    }
  }
}

// Export singleton instance
const userDataService = new UserDataService();
export default userDataService;
