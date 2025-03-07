
import React, { useState, useEffect } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { TranscriptViewer } from '@/components/TranscriptViewer';
import { toast } from 'sonner';

const Index = () => {
  const [minutes, setMinutes] = useState('');
  const [rawTranscript, setRawTranscript] = useState('');

  // Debug function to track minutes content changes
  useEffect(() => {
    console.log('Index component minutes state updated:', minutes ? 'Content available' : 'No content');
  }, [minutes]);

  const handleTranscriptReceived = (transcript: string, formattedMinutes: string) => {
    console.log('handleTranscriptReceived called with:', { 
      transcriptLength: transcript?.length || 0, 
      minutesLength: formattedMinutes?.length || 0
    });
    
    setRawTranscript(transcript);
    
    // If we have formatted minutes, use those. Otherwise, use the transcript.
    if (formattedMinutes && formattedMinutes.trim()) {
      console.log('Setting formatted minutes');
      setMinutes(formattedMinutes);
    } else {
      console.log('No formatted minutes available, using transcript instead');
      setMinutes(transcript);
      toast.warning('No formatted minutes were generated. Showing raw transcript instead.');
    }
  };

  return (
    <div className="min-h-screen p-8 space-y-8">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-2">Meeting Minutes Generator</h1>
        <p className="text-gray-600">Upload your Zoom recording to generate meeting minutes</p>
      </header>
      
      <main className="container mx-auto max-w-4xl">
        <FileUpload onTranscriptReceived={handleTranscriptReceived} />
        <TranscriptViewer transcript={minutes} />
      </main>
    </div>
  );
};

export default Index;
