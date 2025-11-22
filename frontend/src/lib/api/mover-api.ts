import { apiClient } from './client';

export interface OrganizationCreate {
    name: string;
    email: string;
    phone: string;
    business_license_number: string;
    tax_id: string;
    address_line1: string;
    city: string;
    state: string;
    zip_code: string;
}

export interface OrganizationResponse {
    id: string;
    name: string;
    email: string;
    phone: string;
    business_license_number: string;
    tax_id: string;
    address_line1: string;
    city: string;
    state: string;
    zip_code: string;
    status: string;
    created_at: string;
    updated_at: string;
}

export const moverAPI = {
    createOrganization: async (data: OrganizationCreate): Promise<OrganizationResponse> => {
        const response = await apiClient.post<OrganizationResponse>('/api/v1/movers/organizations', data);
        return response.data;
    },
};
