import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Home,
  Users,
  Bell,
  MessageCircle,
  Bookmark,
  User,
  Settings,
  ImageIcon,
  Smile,
  Calendar,
  MapPin,
  Heart,
  Repeat2,
  Share,
  MoreHorizontal
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";

export default function Page() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto flex max-w-7xl">
        {/* Left Sidebar */}
        <div className="border-border sticky top-0 h-screen w-64 overflow-y-auto border-r p-4">
          <nav className="space-y-2">
            <Button variant="ghost" className="w-full justify-start">
              <Home />
              Home
            </Button>
            <Button variant="ghost" className="w-full justify-start">
              <Users />
              Communities
            </Button>
            <Button variant="ghost" className="w-full justify-start">
              <Bell />
              Notifications
            </Button>
            <Button variant="ghost" className="w-full justify-start">
              <MessageCircle />
              Messages
            </Button>
            <Button variant="ghost" className="w-full justify-start">
              <Bookmark />
              Bookmarks
            </Button>
            <Button variant="ghost" className="w-full justify-start">
              <User />
              Profile
            </Button>
            <Button variant="ghost" className="w-full justify-start">
              <Settings />
              Settings
            </Button>
          </nav>

          <Button className="mt-6 w-full">Create Post</Button>

          <div className="mt-8">
            <h3 className="mb-4 text-sm font-semibold">Your Communities</h3>
            <div className="space-y-2">
              <Link href="#" className="flex items-center text-sm">
                <div className="mr-2 h-2 w-2 rounded-full bg-pink-500"></div>
                Design Community
              </Link>
              <Link href="#" className="flex items-center text-sm">
                <div className="mr-2 h-2 w-2 rounded-full bg-blue-500"></div>
                Tech Enthusiasts
              </Link>
              <Link href="#" className="flex items-center text-sm">
                <div className="mr-2 h-2 w-2 rounded-full bg-green-500"></div>
                Sustainability
              </Link>
            </div>
          </div>
        </div>

        {/* Main Timeline */}
        <div className="border-border max-w-2xl flex-1 border-r">
          {/* Post Composer */}
          <div className="border-b p-4">
            <div className="flex space-x-3">
              <Avatar>
                <AvatarImage src="https://bundui-images.netlify.app/avatars/06.png" />
                <AvatarFallback>U</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <Input
                  placeholder="What's happening?"
                  className="placeholder:text-muted-foreground border-none p-0 text-xl focus-visible:ring-0"
                />
                <div className="mt-4 flex items-center justify-between">
                  <div className="flex space-x-1">
                    <Button variant="ghost" size="sm" className="text-blue-500 hover:bg-blue-50">
                      <ImageIcon />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-blue-500 hover:bg-blue-50">
                      <Smile />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-blue-500 hover:bg-blue-50">
                      <Calendar />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-blue-500 hover:bg-blue-50">
                      <MapPin />
                    </Button>
                  </div>
                  <Button variant="outline">Post</Button>
                </div>
              </div>
            </div>
          </div>

          {/* Timeline Posts */}
          <div>
            {/* Post 1 */}
            <div className="border-b p-4">
              <div className="flex space-x-3">
                <Avatar>
                  <AvatarImage src="https://bundui-images.netlify.app/avatars/01.png" />
                  <AvatarFallback>MS</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold">Moyo Shiro</span>
                    <span className="text-muted-foreground">@moyo</span>
                    <span className="text-muted-foreground">·</span>
                    <span className="text-muted-foreground">09:00 AM</span>
                    <Button variant="ghost" size="sm" className="ml-auto">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed">
                    Just launched my new portfolio website! 🚀 Check out these 15 standout examples
                    of creative, sleek, and interactive portfolio designs that inspired me. Which
                    one's your favorite? #WebDesign #PortfolioInspiration
                  </p>
                  <div className="text-muted-foreground mt-3 flex items-center space-x-6">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center space-x-2 hover:text-red-500">
                      <Heart className="h-4 w-4" />
                      <span className="text-sm">62</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center space-x-2 hover:text-green-500">
                      <Repeat2 className="h-4 w-4" />
                      <span className="text-sm">23</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center space-x-2 hover:text-blue-500">
                      <MessageCircle className="h-4 w-4" />
                      <span className="text-sm">45</span>
                    </Button>
                    <Button variant="ghost" size="sm" className="hover:text-blue-500">
                      <Share className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Post 2 */}
            <div className="border-b p-4">
              <div className="flex space-x-3">
                <Avatar>
                  <AvatarImage src="https://bundui-images.netlify.app/avatars/10.png" />
                  <AvatarFallback>S</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold">Sophia</span>
                    <span className="text-muted-foreground">@sophia</span>
                    <span className="text-muted-foreground">·</span>
                    <span className="text-muted-foreground">10:12 AM</span>
                    <Button variant="ghost" size="sm" className="ml-auto">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed">
                    Dreaming of distant worlds... 🪐 This AI-generated image captures the essence of
                    exploration. What stories does it spark in your imagination?
                  </p>
                  <div className="mt-3 overflow-hidden rounded-2xl">
                    <Image
                      src="https://bundui-images.netlify.app/blog/02.jpg"
                      alt="Saturn with rings in space"
                      width={500}
                      height={300}
                      className="w-full object-cover"
                    />
                  </div>
                  <div className="text-muted-foreground mt-3 flex items-center space-x-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center space-x-2 hover:text-red-500">
                      <Heart className="h-4 w-4" />
                      <span className="text-sm">128</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center space-x-2 hover:text-green-500">
                      <Repeat2 className="h-4 w-4" />
                      <span className="text-sm">34</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex items-center space-x-2 hover:text-blue-500">
                      <MessageCircle className="h-4 w-4" />
                      <span className="text-sm">67</span>
                    </Button>
                    <Button variant="ghost" size="sm" className="hover:text-blue-500">
                      <Share className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 space-y-6 p-4">
          {/* Who to Follow */}
          <Card>
            <CardHeader>
              <CardTitle>Who to follow</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src="/placeholder.svg?height=40&width=40" />
                      <AvatarFallback>G</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="text-sm font-semibold">George</p>
                      <p className="text-muted-foreground text-sm">@georgeSZ</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    Follow
                  </Button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src="/placeholder.svg?height=40&width=40" />
                      <AvatarFallback>NS</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="text-sm font-semibold">Nettie Schuster</p>
                      <p className="text-muted-foreground text-sm">@Precious3</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    Follow
                  </Button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src="/placeholder.svg?height=40&width=40" />
                      <AvatarFallback>LR</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="text-sm font-semibold">Mrs. Lola Rohan</p>
                      <p className="text-muted-foreground text-sm">@collin_marks</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    Follow
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trending Topics */}
          <Card>
            <CardHeader>
              <CardTitle>Trending Topics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-blue-600">#TechInnovation</span>
                  <span className="text-muted-foreground text-sm">5.2K posts</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-blue-600">#ArtificialIntelligence</span>
                  <span className="text-muted-foreground text-sm">12K posts</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-blue-600">#ClimateAction</span>
                  <span className="text-muted-foreground text-sm">8.7K posts</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-blue-600">#SpaceExploration</span>
                  <span className="text-muted-foreground text-sm">3.9K posts</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
