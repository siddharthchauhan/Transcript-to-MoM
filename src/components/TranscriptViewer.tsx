import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';

interface TranscriptViewerProps {
  transcript: string;
}

export const TranscriptViewer = ({ transcript }: TranscriptViewerProps) => {
  useEffect(() => {
    // Debug what content we're receiving
    console.log('TranscriptViewer received content:', transcript);
    console.log('Content type:', typeof transcript);
    console.log('Content length:', transcript ? transcript.length : 0);
  }, [transcript]);

  return (
    <Card className="w-full max-w-2xl mx-auto mt-8 p-6">
      <h2 className="text-xl font-semibold mb-4">Meeting Minutes</h2>
      <ScrollArea className="h-[400px] w-full rounded-md border p-4">
        <div className="prose prose-sm max-w-none">
          {transcript ? (
            <div className="whitespace-pre-wrap">
              <ReactMarkdown>{transcript}</ReactMarkdown>
            </div>
          ) : (
            'No transcript available yet. Upload a recording to get started.'
          )}
        </div>
      </ScrollArea>
    </Card>
  );
};
