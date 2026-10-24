"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  Search,
  Heart,
  Shuffle,
  Repeat,
  Menu,
  Home,
  Library,
  Plus,
  User,
  X
} from "lucide-react";

interface Playlist {
  id: string;
  title: string;
  followers: string;
  image: string;
  color: string;
}

interface Track {
  id: string;
  title: string;
  artist: string;
  duration: string;
  image: string;
}

const featuredPlaylists: Playlist[] = [
  {
    id: "1",
    title: "Today's Top Hits",
    followers: "4,223,172 Followers",
    image: "/sunglasses-on-dark-background.png",
    color: "from-slate-900 to-slate-600"
  },
  {
    id: "2",
    title: "Pop Hits",
    followers: "8,823,823 Followers",
    image: "/woman-in-pink-hat.png",
    color: "from-blue-500 to-blue-300"
  },
  {
    id: "3",
    title: "Workout",
    followers: "1,611,732 Followers",
    image: "/fitness-workout-energy.png",
    color: "from-green-600 to-green-400"
  },
  {
    id: "4",
    title: "Chill Hits",
    followers: "768,032 Followers",
    image: "/relaxing-sunset-vibes.png",
    color: "from-orange-500 to-orange-300"
  },
  {
    id: "5",
    title: "Sad Feeling",
    followers: "2,122,820 Followers",
    image: "/melancholy-ocean-scene.png",
    color: "from-gray-600 to-gray-400"
  },
  {
    id: "6",
    title: "Friday's Love Hits",
    followers: "827,783 Followers",
    image: "/romantic-silhouette-sunset.png",
    color: "from-rose-900 to-rose-700"
  }
];

const userPlaylists: Playlist[] = [
  {
    id: "7",
    title: "All is R&B",
    followers: "56 Songs",
    image: "/letter-r-typography.png",
    color: "from-green-600 to-green-400"
  },
  {
    id: "8",
    title: "This is Maroon 5",
    followers: "36 Songs",
    image: "/maroon-5-band-member.png",
    color: "from-black to-gray-800"
  },
  {
    id: "9",
    title: "Acoustic Songs",
    followers: "41 Songs",
    image: "/acoustic-guitar-player.png",
    color: "from-blue-300 to-blue-100"
  },
  {
    id: "10",
    title: "Fresh Songs",
    followers: "22 Songs",
    image: "/fresh-modern-artist.png",
    color: "from-orange-400 to-orange-200"
  },
  {
    id: "11",
    title: "Classic Hits",
    followers: "44 Songs",
    image: "/vinyl-record-classic.png",
    color: "from-teal-600 to-teal-400"
  },
  {
    id: "12",
    title: "Best Night Hits",
    followers: "52 Songs",
    image: "/night-city-lights-music.png",
    color: "from-indigo-900 to-indigo-700"
  }
];

const currentTrack: Track = {
  id: "1",
  title: "Shallow",
  artist: "Lady Gaga",
  duration: "4:56",
  image: "/lady-gaga-shallow-album-cover.png"
};

export function MusicApp() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState("1:24");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="bg-background text-foreground relative flex h-screen">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } bg-sidebar border-sidebar-border fixed z-50 h-full w-64 border-r transition-transform duration-300 lg:relative lg:z-auto lg:translate-x-0`}>
        <div className="p-4">
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="text-sidebar-foreground hover:bg-sidebar-accent lg:hidden">
                <X className="h-5 w-5" />
              </Button>
              <h1 className="text-sidebar-foreground text-xl font-bold">Maise</h1>
            </div>
          </div>

          <div className="space-y-6">
            {/* User Profile */}
            <div className="bg-sidebar-accent flex items-center gap-3 rounded-lg p-2">
              <div className="bg-sidebar-primary flex h-8 w-8 items-center justify-center rounded-full">
                <User className="text-sidebar-primary-foreground h-4 w-4" />
              </div>
              <div className="flex-1">
                <p className="text-sidebar-foreground text-sm font-medium">Vladimir Raksha</p>
                <p className="text-sidebar-foreground/70 text-xs">Premium Plan</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="space-y-2">
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <Home className="mr-3 h-4 w-4" />
                Storage
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <Library className="mr-3 h-4 w-4" />
                News
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <Play className="mr-3 h-4 w-4" />
                Movies
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-primary bg-sidebar-accent w-full justify-start">
                <Volume2 className="mr-3 h-4 w-4" />
                Music
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <Plus className="mr-3 h-4 w-4" />
                Travel
              </Button>
            </nav>

            <Separator className="bg-sidebar-border" />

            <nav className="space-y-2">
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <User className="mr-3 h-4 w-4" />
                Account
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <Menu className="mr-3 h-4 w-4" />
                Settings
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <Heart className="mr-3 h-4 w-4" />
                Help & Support
              </Button>
              <Button
                variant="ghost"
                className="text-sidebar-foreground hover:bg-sidebar-accent w-full justify-start">
                <SkipForward className="mr-3 h-4 w-4" />
                Log Out
              </Button>
            </nav>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header */}
        <header className="border-border border-b p-4 lg:p-6">
          <div className="mb-4 flex items-center justify-between lg:mb-6">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden">
                <Menu className="h-5 w-5" />
              </Button>
              <nav className="hidden space-x-4 md:flex lg:space-x-8">
                <Button
                  variant="ghost"
                  className="text-primary border-primary border-b-2 font-medium">
                  Browse
                </Button>
                <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                  Categories
                </Button>
                <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                  Charts
                </Button>
                <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                  For You
                </Button>
                <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                  New Releases
                </Button>
              </nav>
            </div>
            <div className="relative">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform" />
              <Input
                placeholder="Search..."
                className="bg-input border-border w-32 pl-10 sm:w-48 lg:w-64"
              />
            </div>
          </div>
        </header>

        {/* Content */}
        <ScrollArea className="flex-1 p-4 lg:p-6">
          <div className="space-y-6 lg:space-y-8">
            {/* Browse Section */}
            <section>
              <div className="mb-4 flex items-center justify-between lg:mb-6">
                <h2 className="text-foreground text-xl font-bold lg:text-2xl">Browse</h2>
                <div className="hidden gap-2 sm:flex">
                  <Button variant="ghost" size="icon">
                    <SkipBack className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <SkipForward className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 lg:gap-4">
                {featuredPlaylists.map((playlist) => (
                  <Card
                    key={playlist.id}
                    className="group hover:bg-card/80 cursor-pointer transition-colors">
                    <CardContent className="p-3 lg:p-4">
                      <div
                        className={`relative mb-3 overflow-hidden rounded-lg bg-gradient-to-br lg:mb-4 ${playlist.color}`}>
                        <img
                          src={playlist.image || "/placeholder.svg"}
                          alt={playlist.title}
                          className="aspect-square w-full object-cover mix-blend-overlay"
                        />
                        <Button
                          size="icon"
                          className="bg-primary hover:bg-primary/90 absolute right-2 bottom-2 opacity-0 transition-opacity group-hover:opacity-100">
                          <Play className="text-primary-foreground h-4 w-4" />
                        </Button>
                      </div>
                      <h3 className="text-card-foreground mb-1 text-sm font-semibold text-balance lg:text-base">
                        {playlist.title}
                      </h3>
                      <p className="text-muted-foreground text-xs lg:text-sm">
                        {playlist.followers}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* My Playlists Section */}
            <section>
              <div className="mb-4 flex items-center justify-between lg:mb-6">
                <h2 className="text-foreground text-xl font-bold lg:text-2xl">My Playlists</h2>
                <div className="hidden gap-2 sm:flex">
                  <Button variant="ghost" size="icon">
                    <SkipBack className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <SkipForward className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 lg:gap-4">
                {userPlaylists.map((playlist) => (
                  <Card
                    key={playlist.id}
                    className="group hover:bg-card/80 cursor-pointer transition-colors">
                    <CardContent className="p-3 lg:p-4">
                      <div
                        className={`relative mb-3 overflow-hidden rounded-lg bg-gradient-to-br lg:mb-4 ${playlist.color}`}>
                        <img
                          src={playlist.image || "/placeholder.svg"}
                          alt={playlist.title}
                          className="aspect-square w-full object-cover mix-blend-overlay"
                        />
                        <Button
                          size="icon"
                          className="bg-primary hover:bg-primary/90 absolute right-2 bottom-2 opacity-0 transition-opacity group-hover:opacity-100">
                          <Play className="text-primary-foreground h-4 w-4" />
                        </Button>
                      </div>
                      <h3 className="text-card-foreground mb-1 text-sm font-semibold text-balance lg:text-base">
                        {playlist.title}
                      </h3>
                      <p className="text-muted-foreground text-xs lg:text-sm">
                        {playlist.followers}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* More Like Lady Gaga Section */}
            <section>
              <div className="mb-4 flex items-center justify-between lg:mb-6">
                <h2 className="text-foreground text-xl font-bold lg:text-2xl">
                  More Like Lady Gaga
                </h2>
                <div className="hidden gap-2 sm:flex">
                  <Button variant="ghost" size="icon">
                    <SkipBack className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <SkipForward className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-4 lg:gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="flex-shrink-0">
                    <div className="mb-3 h-24 w-24 cursor-pointer overflow-hidden rounded-full transition-transform hover:scale-105 lg:h-32 lg:w-32">
                      <img
                        src={`/music-artist.png?height=128&width=128&query=music artist ${i + 1}`}
                        alt={`Artist ${i + 1}`}
                        className="h-full w-full object-cover"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </ScrollArea>

        {/* Music Player */}
        <div className="border-border bg-card border-t p-3 lg:p-4">
          <div className="flex items-center justify-between gap-2 lg:gap-4">
            <div className="flex min-w-0 flex-1 items-center gap-2 lg:flex-none lg:gap-4">
              <img
                src={currentTrack.image || "/placeholder.svg"}
                alt={currentTrack.title}
                className="h-10 w-10 flex-shrink-0 rounded-lg object-cover lg:h-12 lg:w-12"
              />
              <div className="min-w-0 flex-1 lg:flex-none">
                <h4 className="text-card-foreground truncate text-sm font-medium lg:text-base">
                  {currentTrack.title}
                </h4>
                <p className="text-muted-foreground truncate text-xs lg:text-sm">
                  {currentTrack.artist}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-primary flex-shrink-0">
                <Heart className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex max-w-md flex-1 flex-col items-center gap-1 lg:gap-2">
              <div className="flex items-center gap-2 lg:gap-4">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground hidden sm:flex">
                  <Shuffle className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground">
                  <SkipBack className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground">
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground">
                  <SkipForward className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground hidden sm:flex">
                  <Repeat className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex w-full items-center gap-2">
                <span className="text-muted-foreground text-xs">{currentTime}</span>
                <div className="bg-muted h-1 flex-1 rounded-full">
                  <div className="bg-primary h-full w-1/3 rounded-full"></div>
                </div>
                <span className="text-muted-foreground text-xs">{currentTrack.duration}</span>
              </div>
            </div>

            <div className="hidden items-center gap-2 lg:flex">
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-foreground">
                <Volume2 className="h-4 w-4" />
              </Button>
              <div className="bg-muted h-1 w-20 rounded-full">
                <div className="bg-primary h-full w-3/4 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
