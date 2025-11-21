import { calendarAPI } from "@/lib/api/calendar-api";
import { apiClient } from "@/lib/api/client";

// Mock the apiClient
jest.mock("@/lib/api/client");
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe("Calendar API", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe("getCalendarBookings", () => {
        it("fetches calendar bookings successfully", async () => {
            const mockResponse = {
                start_date: "2025-01-01",
                end_date: "2025-01-31",
                bookings: [
                    {
                        id: "booking-1",
                        booking_number: "BK-12345",
                        customer_name: "John Doe",
                        customer_phone: "1234567890",
                        move_date: "2025-01-15T10:00:00Z",
                        pickup_address: "123 Main St",
                        dropoff_address: "456 Oak Ave",
                        estimated_duration_hours: 4,
                        status: "scheduled",
                        assigned_driver_id: "driver-1",
                        assigned_driver_name: "Jane Smith",
                        assigned_truck_id: "truck-1",
                        assigned_truck_identifier: "TRK-001",
                        notes: null,
                    },
                ],
                total_bookings: 1,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            const result = await calendarAPI.getCalendarBookings(
                "2025-01-01",
                "2025-01-31"
            );

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining("/api/v1/calendar/bookings")
            );
            expect(result).toEqual(mockResponse);
        });

        it("includes status filter in request", async () => {
            const mockResponse = {
                start_date: "2025-01-01",
                end_date: "2025-01-31",
                bookings: [],
                total_bookings: 0,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            await calendarAPI.getCalendarBookings("2025-01-01", "2025-01-31", [
                "scheduled",
                "in_progress",
            ]);

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining("status_filter=scheduled")
            );
        });
    });

    describe("getDriverSchedule", () => {
        it("fetches driver schedule successfully", async () => {
            const mockResponse = {
                driver_id: "driver-1",
                driver_name: "Jane Smith",
                start_date: "2025-01-01",
                end_date: "2025-01-31",
                schedule: [
                    {
                        driver_id: "driver-1",
                        driver_name: "Jane Smith",
                        driver_phone: "9876543210",
                        booking_id: "booking-1",
                        booking_number: "BK-12345",
                        start_time: "2025-01-15T10:00:00Z",
                        end_time: "2025-01-15T14:00:00Z",
                        status: "scheduled",
                        customer_name: "John Doe",
                        pickup_address: "123 Main St",
                        dropoff_address: "456 Oak Ave",
                    },
                ],
                total_hours_booked: 4,
                total_bookings: 1,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            const result = await calendarAPI.getDriverSchedule(
                "driver-1",
                "2025-01-01",
                "2025-01-31"
            );

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining(
                    "/api/v1/calendar/driver/driver-1/schedule"
                )
            );
            expect(result).toEqual(mockResponse);
        });
    });

    describe("getTruckSchedule", () => {
        it("fetches truck schedule successfully", async () => {
            const mockResponse = {
                truck_id: "truck-1",
                truck_identifier: "TRK-001",
                start_date: "2025-01-01",
                end_date: "2025-01-31",
                schedule: [
                    {
                        truck_id: "truck-1",
                        truck_identifier: "TRK-001",
                        booking_id: "booking-1",
                        booking_number: "BK-12345",
                        start_time: "2025-01-15T10:00:00Z",
                        end_time: "2025-01-15T14:00:00Z",
                        status: "scheduled",
                        customer_name: "John Doe",
                        pickup_address: "123 Main St",
                        dropoff_address: "456 Oak Ave",
                    },
                ],
                total_hours_booked: 4,
                total_bookings: 1,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            const result = await calendarAPI.getTruckSchedule(
                "truck-1",
                "2025-01-01",
                "2025-01-31"
            );

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining(
                    "/api/v1/calendar/truck/truck-1/schedule"
                )
            );
            expect(result).toEqual(mockResponse);
        });
    });

    describe("getFleetCalendar", () => {
        it("fetches fleet calendar successfully", async () => {
            const mockResponse = {
                org_id: "org-1",
                start_date: "2025-01-01",
                end_date: "2025-01-31",
                bookings: [],
                driver_schedules: [],
                truck_schedules: [],
                total_bookings: 0,
                total_drivers: 5,
                total_trucks: 3,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            const result = await calendarAPI.getFleetCalendar(
                "2025-01-01",
                "2025-01-31"
            );

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining("/api/v1/calendar/fleet")
            );
            expect(result).toEqual(mockResponse);
        });
    });

    describe("checkAvailability", () => {
        it("checks availability successfully", async () => {
            const mockResponse = {
                is_available: true,
                available_slots: [
                    {
                        start_time: "2025-01-15T09:00:00Z",
                        end_time: "2025-01-15T17:00:00Z",
                        available_drivers: ["driver-1", "driver-2"],
                        available_trucks: ["truck-1", "truck-2"],
                    },
                ],
                total_available_drivers: 2,
                total_available_trucks: 2,
                message: null,
            };

            mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

            const request = {
                org_id: "org-1",
                date: "2025-01-15",
                estimated_duration_hours: 4,
                require_driver: true,
                require_truck: true,
            };

            const result = await calendarAPI.checkAvailability(request);

            expect(mockedApiClient.post).toHaveBeenCalledWith(
                "/api/v1/calendar/availability",
                request
            );
            expect(result).toEqual(mockResponse);
        });

        it("handles no availability", async () => {
            const mockResponse = {
                is_available: false,
                available_slots: [],
                total_available_drivers: 0,
                total_available_trucks: 0,
                message: "No resources available for the requested time slot",
            };

            mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

            const request = {
                org_id: "org-1",
                date: "2025-01-15",
                estimated_duration_hours: 4,
            };

            const result = await calendarAPI.checkAvailability(request);

            expect(result.is_available).toBe(false);
            expect(result.message).toBeTruthy();
        });
    });

    describe("Error Handling", () => {
        it("handles API errors", async () => {
            const mockError = new Error("Network error");
            mockedApiClient.get.mockRejectedValueOnce(mockError);

            await expect(
                calendarAPI.getCalendarBookings("2025-01-01", "2025-01-31")
            ).rejects.toThrow("Network error");
        });
    });
});
