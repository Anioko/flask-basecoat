"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { productFormSchema, type ProductFormData } from "./validation";
import { PlusIcon, XIcon } from "lucide-react";

export default function Page() {
  const [categories, setCategories] = useState<string[]>(["Headphones"]);
  const [newCategory, setNewCategory] = useState("");
  const [variations, setVariations] = useState<Array<{ type: string; value: string }>>([]);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors }
  } = useForm<ProductFormData>({
    resolver: zodResolver(productFormSchema),
    defaultValues: {
      name: "",
      description: "",
      status: "published",
      categories: ["Headphones"],
      tags: [],
      variations: [],
      basePrice: "",
      discountType: "none",
      template: "default",
      taxClass: "standard",
      vatAmount: ""
    }
  });

  const onSubmit = (data: ProductFormData) => {
    console.log("Form submitted:", data);
    // Handle form submission here
  };

  const addCategory = () => {
    if (newCategory && !categories.includes(newCategory)) {
      const updatedCategories = [...categories, newCategory];
      setCategories(updatedCategories);
      setValue("categories", updatedCategories);
      setNewCategory("");
    }
  };

  const removeCategory = (category: string) => {
    const updatedCategories = categories.filter((c) => c !== category);
    setCategories(updatedCategories);
    setValue("categories", updatedCategories);
  };

  const addVariation = () => {
    const newVariation = { type: "Size", value: "" };
    const updatedVariations = [...variations, newVariation];
    setVariations(updatedVariations);
    setValue("variations", updatedVariations);
  };

  const removeVariation = (index: number) => {
    const updatedVariations = variations.filter((_, i) => i !== index);
    setVariations(updatedVariations);
    setValue("variations", updatedVariations);
  };

  const updateVariation = (index: number, field: "type" | "value", value: string) => {
    const updatedVariations = variations.map((variation, i) =>
      i === index ? { ...variation, [field]: value } : variation
    );
    setVariations(updatedVariations);
    setValue("variations", updatedVariations);
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left Column - Main Content */}
          <div className="space-y-4 lg:col-span-2">
            {/* General Section */}
            <Card>
              <CardHeader>
                <CardTitle>General</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    Product Name <span className="text-red-500">*</span>
                  </Label>
                  <Input id="name" placeholder="Product Name" {...register("name")} />
                  {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
                  <p className="text-muted-foreground text-sm">
                    A product name is required and recommended to be unique.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Set a description to the product for better visibility."
                    className="min-h-[200px]"
                    {...register("description")}
                  />
                  {errors.description && (
                    <p className="text-sm text-red-500">{errors.description.message}</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Media Section */}
            <Card>
              <CardHeader>
                <CardTitle>Media</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border-2 border-dashed border-purple-300 bg-purple-50 p-12 text-center">
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center text-2xl text-purple-400">
                    📁
                  </div>
                  <p className="text-purple-600">Drop files here to upload</p>
                </div>
              </CardContent>
            </Card>

            {/* Variation Section */}
            <Card>
              <CardHeader>
                <CardTitle>Variation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <Label>Add Product Variations</Label>
                  {variations.map((variation, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <Select
                        value={variation.type}
                        onValueChange={(value) => updateVariation(index, "type", value)}>
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Size">Size</SelectItem>
                          <SelectItem value="Color">Color</SelectItem>
                          <SelectItem value="Material">Material</SelectItem>
                        </SelectContent>
                      </Select>
                      <Input
                        placeholder="Variation"
                        value={variation.value}
                        onChange={(e) => updateVariation(index, "value", e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => removeVariation(index)}>
                        <XIcon />
                      </Button>
                    </div>
                  ))}
                  <Button type="button" variant="outline" onClick={addVariation}>
                    <PlusIcon /> Add another variation
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Pricing Section */}
            <Card>
              <CardHeader>
                <CardTitle>Pricing</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="basePrice">
                    Base Price <span className="text-red-500">*</span>
                  </Label>
                  <Input id="basePrice" placeholder="Product Price" {...register("basePrice")} />
                  {errors.basePrice && (
                    <p className="text-sm text-red-500">{errors.basePrice.message}</p>
                  )}
                  <p className="text-muted-foreground text-sm">Set the product price.</p>
                </div>

                <div className="space-y-2">
                  <Label>Discount Type</Label>
                  <RadioGroup defaultValue="none" className="flex gap-8">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="none" id="no-discount" {...register("discountType")} />
                      <Label htmlFor="no-discount">No Discount</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem
                        value="percentage"
                        id="percentage"
                        {...register("discountType")}
                      />
                      <Label htmlFor="percentage">Percentage %</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem
                        value="fixed"
                        id="fixed-price"
                        {...register("discountType")}
                      />
                      <Label htmlFor="fixed-price">Fixed Price</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="taxClass">
                      Tax Class <span className="text-red-500">*</span>
                    </Label>
                    <Select>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select an option" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard</SelectItem>
                        <SelectItem value="reduced">Reduced</SelectItem>
                        <SelectItem value="zero">Zero Rate</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-muted-foreground text-sm">Set the product tax class.</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="vatAmount">
                      VAT Amount (%) <span className="text-red-500">*</span>
                    </Label>
                    <Input id="vatAmount" placeholder="0" {...register("vatAmount")} />
                    {errors.vatAmount && (
                      <p className="text-sm text-red-500">{errors.vatAmount.message}</p>
                    )}
                    <p className="text-muted-foreground text-sm">Set the product VAT about.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-4">
            {/* Thumbnail Section */}
            <Card>
              <CardHeader>
                <CardTitle>Thumbnail</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border-2 border-dashed border-purple-300 bg-purple-50 p-8 text-center">
                  <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center text-xl text-purple-400">
                    🖼️
                  </div>
                  <p className="text-sm text-purple-600">Drop Thumbnail here to upload</p>
                </div>
                <p className="text-muted-foreground mt-2 text-xs">
                  Set the product thumbnail image. Only *.png, *.jpg and *.jpeg image files are
                  accepted.
                </p>
              </CardContent>
            </Card>

            {/* Status Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Status
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                </CardTitle>
                <CardDescription>Set the product status.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Select defaultValue="published">
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="published">Published</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Product Details Section */}
            <Card>
              <CardHeader>
                <CardTitle>Product Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label className="text-sm font-medium">Categories</Label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {categories.map((category) => (
                      <Badge
                        key={category}
                        variant="secondary"
                        className="bg-purple-100 text-purple-700">
                        <span
                          className="mr-1 cursor-pointer"
                          onClick={() => removeCategory(category)}>
                          ×
                        </span>
                        {category}
                      </Badge>
                    ))}
                  </div>
                  <p className="text-muted-foreground mt-1 text-xs">Add product to a category.</p>
                  <div className="mt-2 flex gap-2">
                    <Input
                      placeholder="New category"
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      className="flex-1"
                    />
                    <Button type="button" variant="outline" onClick={addCategory}>
                      <PlusIcon /> Create New Category
                    </Button>
                  </div>
                </div>

                <Separator />

                <div>
                  <Label className="text-sm font-medium">Tags</Label>
                  <p className="text-muted-foreground mt-1 text-xs">Add product to a category.</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Product Template</CardTitle>
                <CardDescription>
                  Assign a template from your current theme to define how a single product is
                  displayed.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Select defaultValue="default">
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default Template</SelectItem>
                      <SelectItem value="minimal">Minimal Template</SelectItem>
                      <SelectItem value="detailed">Detailed Template</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="flex gap-3">
          <Button type="submit">Save changes</Button>
          <Button type="button" variant="destructive">
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
