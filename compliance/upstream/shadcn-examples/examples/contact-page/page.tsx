"use client";

import { useState } from "react";
import { User, Phone, Mail, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import Link from "next/link";

const Contact = () => {
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    phone: "",
    email: "",
    message: "",
    agreedToPrivacy: false
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Reset form
    setFormData({
      firstName: "",
      lastName: "",
      phone: "",
      email: "",
      message: "",
      agreedToPrivacy: false
    });
  };

  const handleChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="bg-background min-h-screen">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid items-start gap-16 lg:grid-cols-2">
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-foreground text-3xl leading-tight font-bold lg:text-4xl">
                Let&#39;s Talk About
                <br />
                Your Energy Goals
              </h1>
              <p className="text-muted-foreground leading-relaxed">
                Whether You&#39;re Curious About Solar, Ready To Get Your Energy System, Or Just
                Need Some Honest Guidance—Our Experts Are Here To Help.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="relative">
                  <User className="text-muted-foreground absolute top-3 left-3 h-5 w-5" />
                  <Input
                    placeholder="First Name"
                    value={formData.firstName}
                    onChange={(e) => handleChange("firstName", e.target.value)}
                    className="border-border bg-card h-12 pl-10"
                    required
                  />
                </div>
                <div className="relative">
                  <User className="text-muted-foreground absolute top-3 left-3 h-5 w-5" />
                  <Input
                    placeholder="Last Name"
                    value={formData.lastName}
                    onChange={(e) => handleChange("lastName", e.target.value)}
                    className="border-border bg-card h-12 pl-10"
                    required
                  />
                </div>
              </div>

              <div className="relative">
                <Phone className="text-muted-foreground absolute top-3 left-3 h-5 w-5" />
                <Input
                  placeholder="Phone No"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange("phone", e.target.value)}
                  className="border-border bg-card h-12 pl-10"
                  required
                />
              </div>

              <div className="relative">
                <Mail className="text-muted-foreground absolute top-3 left-3 h-5 w-5" />
                <Input
                  placeholder="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  className="border-border bg-card h-12 pl-10"
                  required
                />
              </div>

              <div>
                <Textarea
                  placeholder="Your message"
                  value={formData.message}
                  onChange={(e) => handleChange("message", e.target.value)}
                  className="border-border bg-card min-h-32 resize-none"
                  required
                />
              </div>

              <div className="flex items-center space-x-3">
                <Checkbox
                  id="privacy"
                  checked={formData.agreedToPrivacy}
                  onCheckedChange={(checked) => handleChange("agreedToPrivacy", checked)}
                />
                <label htmlFor="privacy" className="text-muted-foreground text-sm leading-relaxed">
                  I have read and agree to the{" "}
                  <Link href="#" className="underline">
                    privacy policy
                  </Link>
                </label>
              </div>

              <Button type="submit" size="lg">
                Send Your Message
              </Button>
            </form>
          </div>

          {/* Right Column - Hero Image */}
          <div className="relative">
            <div className="overflow-hidden rounded-2xl shadow-lg">
              <img
                src="https://plus.unsplash.com/premium_photo-1716603741447-7fcd7ddeba39?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
                alt="Wind turbine over coastal landscape representing sustainable energy solutions"
                className="h-[600px] w-full object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;
