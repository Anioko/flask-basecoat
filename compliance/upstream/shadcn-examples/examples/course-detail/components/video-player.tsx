"use client";

import { useState } from "react";
import { Play, Pause, Volume2, Maximize, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function VideoPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <Card className="overflow-hidden py-0">
      <div className="from-muted to-muted/50 relative aspect-video bg-gradient-to-br">
        {/* Video placeholder with instructor image */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 to-slate-800">
          <img
            src="https://plus.unsplash.com/premium_photo-1682126202084-f23c6cee5dbc?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
            alt="Course instructor"
            className="h-full w-full object-cover"
          />
        </div>

        {/* Video Controls Overlay */}
        <div className="absolute inset-0 bg-black/20 opacity-0 transition-opacity duration-200 hover:opacity-100">
          <div className="absolute right-4 bottom-4 left-4">
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <Button
                  size="sm"
                  variant="secondary"
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={() => setIsPlaying(!isPlaying)}>
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
                <span className="text-sm font-medium">0:23 / 45:32</span>
              </div>

              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost" className="text-white hover:bg-white/20">
                  <Volume2 className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="ghost" className="text-white hover:bg-white/20">
                  <Settings className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="ghost" className="text-white hover:bg-white/20">
                  <Maximize className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
