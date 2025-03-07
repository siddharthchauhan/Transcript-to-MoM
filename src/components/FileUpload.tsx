import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileVideo, Check } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { uploadRecordingForTranscription, checkTranscriptionStatus } from '@/services/transcriptionService';
import { toast } from 'sonner';

interface FileUploadProps {
  onTranscriptReceived: (transcript: string, minutes: string) => void;
}

export const FileUpload = ({ onTranscriptReceived }: FileUploadProps) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setIsUploading(true);
      setUploadProgress(0);
      
      // Simulate upload progress while actually uploading
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);
      
      try {
        // Upload file and get job ID
        const uploadResponse = await uploadRecordingForTranscription(file);
        clearInterval(progressInterval);
        setUploadProgress(100);
        setIsUploading(false);
        setIsProcessing(true);
        
        // If we have a job ID, start polling for status
        if (uploadResponse.job_id) {
          toast.info("Processing your recording. This may take a few moments...");
          const jobId = uploadResponse.job_id;
          
          // Poll for job status
          const pollInterval = setInterval(async () => {
            try {
              const statusResponse = await checkTranscriptionStatus(jobId);
              
              // Check if processing is complete
              if (statusResponse.status === 'completed') {
                clearInterval(pollInterval);
                setIsProcessing(false);
                
                console.log('Completed job data:', statusResponse);
                console.log('Minutes content:', statusResponse.minutes);
                
                if (statusResponse.transcript) {
                  // Ensure minutes is a string, even if null or undefined
                  const formattedMinutes = statusResponse.minutes || '';
                  console.log('Passing minutes to viewer:', formattedMinutes);
                  
                  onTranscriptReceived(statusResponse.transcript, formattedMinutes);
                  toast.success("Transcription complete!");
                }
              } 
              // Check for errors
              else if (statusResponse.status === 'error') {
                clearInterval(pollInterval);
                setIsProcessing(false);
                toast.error(`Processing failed: ${statusResponse.error || 'Unknown error'}`);
              }
              // Still processing, continue polling
              else if (['queued', 'transcribing', 'generating_minutes'].includes(statusResponse.status)) {
                console.log(`Job status: ${statusResponse.status}`);
              }
            } catch (pollError) {
              console.error("Error checking job status:", pollError);
              // Don't clear interval on transient errors
            }
          }, 3000); // Poll every 3 seconds
        }
      } catch (error) {
        clearInterval(progressInterval);
        setIsUploading(false);
        setIsProcessing(false);
        console.error("Upload failed:", error);
        toast.error("Failed to upload recording");
      }
    }
  }, [onTranscriptReceived]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/mp4': ['.mp4'],
      'video/webm': ['.webm'],
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav']
    },
    maxFiles: 1,
    disabled: isUploading || isProcessing
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={cn(
          "drop-zone",
          isDragActive && "dragging",
          (isUploading || isProcessing) && "pointer-events-none opacity-50"
        )}
      >
        <input {...getInputProps()} />
        <div className="text-center">
          {!isUploading && !isProcessing ? (
            <>
              <Upload className="w-12 h-12 mx-auto mb-4" />
              <p className="text-xl font-medium mb-2">Drop your recording here</p>
              <p className="text-sm text-gray-500">
                or click to select a file (MP4, WEBM, MP3, WAV)
              </p>
            </>
          ) : isUploading ? (
            <>
              <FileVideo className="w-12 h-12 mx-auto mb-4" />
              <Progress value={uploadProgress} className="w-64 mx-auto mb-4" />
              <p className="text-sm text-gray-500">
                {uploadProgress < 100 ? "Uploading..." : "Processing..."}
              </p>
            </>
          ) : (
            <>
              <FileVideo className="w-12 h-12 mx-auto mb-4" />
              <p className="text-sm text-gray-500">Processing your recording...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
