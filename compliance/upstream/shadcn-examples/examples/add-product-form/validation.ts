import { z } from "zod";

export const productFormSchema = z.object({
  name: z.string().min(1, "Product name is required"),
  description: z.string().optional(),
  status: z.enum(["published", "draft", "archived"]),
  categories: z.array(z.string()),
  tags: z.array(z.string()),
  variations: z.array(
    z.object({
      type: z.string(),
      value: z.string()
    })
  ),
  basePrice: z.string().min(1, "Base price is required"),
  discountType: z.enum(["none", "percentage", "fixed"]),
  template: z.enum(["default", "minimal", "detailed"]),
  taxClass: z.enum(["standard", "reduced", "zero"]),
  vatAmount: z.string().min(1, "VAT amount is required")
});

export type ProductFormData = z.infer<typeof productFormSchema>;
