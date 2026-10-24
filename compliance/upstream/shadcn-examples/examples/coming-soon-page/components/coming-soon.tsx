import Link from "next/link";
import { Share2, Facebook, Twitter, Linkedin } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Countdown } from "./countdown";
import { Logo } from "@/components/logo";
import Image from "next/image";

export default function ComingSoon() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left Section */}
      <div className="posi relative flex flex-1 flex-col items-center justify-between bg-[url(/coming-soon.jpg)] bg-cover bg-top p-8 lg:p-12">
        <div className="z-10 flex w-full items-center justify-start">
          <div className="flex items-center gap-2">
            <Image
              src={`${process.env.BASE_URL ?? process.env.NEXT_PUBLIC_BASE_URL}/logo.png`}
              width={30}
              height={28}
              alt="..."
            />
            <span className="text-lg font-medium text-black">Logo</span>
          </div>
        </div>

        <nav className="relative z-10 mt-8 flex w-full justify-center gap-6 text-gray-600 lg:justify-start">
          <Link href="#" className="text-black hover:underline">
            About
          </Link>
          <Link href="#" className="text-black hover:underline">
            Contact
          </Link>
          <Link href="#" className="text-black hover:underline">
            Feedback
          </Link>
          <Link href="#" className="text-black hover:underline">
            Help
          </Link>
        </nav>
      </div>

      {/* Right Section */}
      <div className="relative flex flex-1 flex-col items-center justify-between bg-gradient-to-br p-8 lg:p-12">
        <div className="flex w-full items-center justify-end">
          <Share2 className="h-6 w-6 cursor-pointer opacity-80 hover:opacity-100" />
        </div>

        <div className="flex flex-col items-center space-y-20 text-center">
          <div className="relative z-10 flex flex-col items-center space-y-2 text-center">
            <h1 className="text-4xl font-bold text-[#6a5acd] lg:text-5xl">Coming Soon</h1>
            <p className="text-muted-foreground lg:text-lg">Stay Connected, Stay Updated!</p>
          </div>

          <Countdown />

          <div className="space-y-6">
            <h2 className="text-xl font-semibold md:text-2xl">Get Updates!</h2>
            <form className="flex w-full max-w-sm rounded-full border p-1">
              <Input
                type="email"
                placeholder="Email Address"
                className="flex-1 rounded-full border-none bg-transparent px-4 focus-visible:ring-0 focus-visible:ring-offset-0"
              />
              <Button type="submit" className="rounded-full">
                Send Now
              </Button>
            </form>
          </div>
        </div>

        <div className="flex w-full justify-center gap-6 lg:justify-end">
          <Link href="#" aria-label="Facebook">
            <Facebook className="h-6 w-6 text-white opacity-80 hover:opacity-100" />
          </Link>
          <Link href="#" aria-label="Twitter">
            <Twitter className="h-6 w-6 text-white opacity-80 hover:opacity-100" />
          </Link>
          <Link href="#" aria-label="LinkedIn">
            <Linkedin className="h-6 w-6 text-white opacity-80 hover:opacity-100" />
          </Link>
        </div>
      </div>
    </div>
  );
}
