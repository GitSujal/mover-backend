import { apiClient } from './client';

export interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string;
    role: string;
    org_id?: string;
    is_active: boolean;
}

export interface UserLogin {
    email: string;
    password: string;
}

export interface UserRegister {
    first_name: string;
    last_name: string;
    email: string;
    phone?: string;
    password: string;
    role?: string;
    org_id?: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}

export const authAPI = {
    /**
     * Get current logged-in user
     */
    getCurrentUser: async (): Promise<User> => {
        const response = await apiClient.get<User>('/api/v1/auth/me');
        return response.data;
    },

    /**
     * Login with email and password
     */
    login: async (credentials: UserLogin): Promise<TokenResponse> => {
        const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', credentials);
        return response.data;
    },

    /**
     * Register a new mover user
     */
    register: async (userData: UserRegister): Promise<TokenResponse> => {
        const response = await apiClient.post<TokenResponse>('/api/v1/auth/register', userData);
        return response.data;
    },

    /**
     * Logout (clear tokens from storage)
     */
    logout: () => {
        // Clear tokens from localStorage
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    },

    /**
     * Store tokens in localStorage
     */
    storeTokens: (tokens: TokenResponse) => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', tokens.access_token);
            localStorage.setItem('refresh_token', tokens.refresh_token);
        }
    },

    /**
     * Get access token from localStorage
     */
    getAccessToken: (): string | null => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('access_token');
        }
        return null;
    },
};
