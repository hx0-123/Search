/**
 * Event Bus
 * Used for inter-component communication to avoid performance issues caused by watch listeners
 */

type EventCallback = (...args: any[]) => void;

class EventBus {
  private events: Map<string, EventCallback[]> = new Map();

  /**
   * Subscribe to event
   */
  on(event: string, callback: EventCallback): void {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    
    const callbacks = this.events.get(event)!;
    
    // Prevent duplicate subscription
    if (callbacks.includes(callback)) {
      console.warn(`[EventBus] Callback already registered for "${event}", skipping`);
      return;
    }
    
    callbacks.push(callback);
    console.log(`[EventBus] Registered callback for "${event}", total: ${callbacks.length}`);
  }

  /**
   * Unsubscribe from event
   */
  off(event: string, callback: EventCallback): void {
    const callbacks = this.events.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event (async version, non-blocking)
   */
  emit(event: string, ...args: any[]): void {
    console.log(`[EventBus] emit called for "${event}"`);
    const callbacks = this.events.get(event);
    
    if (!callbacks || callbacks.length === 0) {
      console.log(`[EventBus] No callbacks registered for "${event}"`);
      return;
    }
    
    console.log(`[EventBus] Found ${callbacks.length} callback(s) for "${event}"`);
    
    // Execute all callbacks asynchronously to avoid blocking
    callbacks.forEach((callback, index) => {
      setTimeout(() => {
        try {
          console.log(`[EventBus] Executing callback ${index + 1}/${callbacks.length} for "${event}"`);
          callback(...args);
          console.log(`[EventBus] Callback ${index + 1} completed`);
        } catch (error) {
          console.error(`[EventBus] Error in callback ${index + 1} for "${event}":`, error);
        }
      }, 0);
    });
    
    console.log(`[EventBus] All callbacks scheduled for "${event}"`);
  }

  /**
   * Clear all event listeners
   */
  clear(): void {
    this.events.clear();
  }
  
  /**
   * Get listener count for an event
   */
  getListenerCount(event: string): number {
    const callbacks = this.events.get(event);
    return callbacks ? callbacks.length : 0;
  }
  
  /**
   * Get all events and their listener counts
   */
  getAllListeners(): Record<string, number> {
    const result: Record<string, number> = {};
    this.events.forEach((callbacks, event) => {
      result[event] = callbacks.length;
    });
    return result;
  }
}

// Export singleton instance
export const eventBus = new EventBus();

// Define event name constants
export const Events = {
  SAFE_ZONE_UPDATED: 'safe-zone-updated',
  QUERY_SUBMITTED: 'query-submitted',
  QUERY_UPDATED: 'query-updated',
} as const;

