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

export const authAPI = {
    getCurrentUser: async (): Promise<User> => {
        const response = await apiClient.get<User>('/api/v1/auth/me');
        return response.data;
    },
};
