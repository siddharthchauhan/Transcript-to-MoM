
import { toast } from "sonner";

const API_URL = "http://localhost:8000"; // Change this to your actual backend URL in production

export interface JobStatus {
  job_id: string;
  status: string;
  transcript?: string;
  minutes?: string;
  error?: string;
}

export interface TranscriptResponse extends JobStatus {
  transcript: string;
}

export const uploadRecordingForTranscription = async (file: File): Promise<JobStatus> => {
  try {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await fetch(`${API_URL}/upload`, {
      method: "POST",
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error uploading file:", error);
    toast.error("Failed to upload recording. Please try again.");
    throw error;
  }
};

export const checkTranscriptionStatus = async (jobId: string): Promise<JobStatus> => {
  try {
    const response = await fetch(`${API_URL}/status/${jobId}`);
    
    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error checking transcription status:", error);
    throw error;
  }
};
