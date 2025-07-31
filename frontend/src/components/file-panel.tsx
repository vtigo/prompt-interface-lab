'use client';

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

interface FileItem {
  filename: string;
  size: number;
  content: string;
}

interface FilePanelProps {
  files: FileItem[];
}

export function FilePanel({ files }: FilePanelProps) {
  return (
    <Sheet>
      <SheetTrigger asChild className='cursor-pointer'>
        <Badge variant="secondary">
          Files ({files.length})...
        </Badge>
      </SheetTrigger>
      <SheetContent className="overflow-hidden">
        <SheetHeader>
          <SheetTitle>Files</SheetTitle>
        </SheetHeader>
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto">
            {files.length === 0 ? (
              <div className="text-center text-muted-foreground mt-8">
                <p>No files available</p>
              </div>
            ) : (
              <Accordion type="multiple" className="w-full">
                {files.map((file, index) => (
                  <AccordionItem key={index} value={`file-${index}`}>
                    <AccordionTrigger className="p-3 hover:no-underline hover:bg-accent">
                      <div className="flex items-center justify-between w-full mr-2">
                        <span className="font-medium text-sm truncate">{file.filename}</span>
                        <Badge variant="secondary" className="text-xs">
                          {file.size} bytes
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="p-3 pt-0">
                      <div>
                        <pre className="text-xs px-2 py-4 overflow-y-auto">
                          {file.content}
                        </pre>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
