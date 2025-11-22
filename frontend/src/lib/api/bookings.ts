import { bookingFormSchema } from "@/lib/validations/booking";
import { z } from "zod";

export async function createBooking(data: z.infer<typeof bookingFormSchema>) {
  // TODO: Implement API call to the backend
  console.log("Creating booking with data:", data);
  return { success: true, data };
}

export async function getBooking(id: string) {
  // TODO: Implement API call to the backend
  console.log("Getting booking with id:", id);
  return { success: true, data: { id } };
}
