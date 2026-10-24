"use client";

import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";

import { CartItem } from "./cart-item";
import { CouponSection } from "./coupon-section";
import { OrderSummary } from "./order-summary";
import { PaymentMethods } from "./payment-methods";

const cartData = [
  {
    id: "1",
    name: "Samsung Galaxy S23 Ultra S918B/DS 256GB",
    color: "Phantom Black",
    price: 1049.99,
    quantity: 2,
    image: "https://bundui-images.netlify.app/products/01.jpeg"
  },
  {
    id: "2",
    name: "JBL Charge 3 Waterproof Portable Bluetooth Speaker",
    color: "Black",
    price: 109.99,
    quantity: 1,
    image: "https://bundui-images.netlify.app/products/02.jpeg"
  },
  {
    id: "3",
    name: "GARMIN Fenix 7X 010-02541-11 Exclusive Version",
    color: "Black",
    price: 349.99,
    quantity: 1,
    image: "https://bundui-images.netlify.app/products/03.jpeg"
  },
  {
    id: "4",
    name: "Beats Fit Pro - True Wireless Noise Cancelling Earbuds",
    color: "Phantom Black",
    price: 199.99,
    quantity: 1,
    image: "https://bundui-images.netlify.app/products/04.jpeg"
  },
  {
    id: "5",
    name: "JLab Epic Air Sport ANC True Wireless Earbuds",
    color: "Black",
    price: 99.99,
    quantity: 1,
    image: "https://bundui-images.netlify.app/products/06.jpeg"
  }
];

export type CartItemType = (typeof cartData)[number];

export default function Cart() {
  const [cartItems, setCartItems] = useState<CartItemType[]>(cartData);

  const updateQuantity = (id: string, quantity: number) => {
    setCartItems((items) => items.map((item) => (item.id === id ? { ...item, quantity } : item)));
  };

  const removeItem = (id: string) => {
    setCartItems((items) => items.filter((item) => item.id !== id));
  };

  const handleApplyCoupon = (code: string) => {
    console.log("Applying coupon:", code);
    // Implement coupon logic here
  };

  const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const discount = 0;
  const delivery = 29.99;
  const tax = 39.99;

  return (
    <div className="bg-background min-h-screen p-4 lg:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Shopping Cart Section */}
          <div className="lg:col-span-2">
            <div className="bg-card border-cart-border rounded-lg border p-6">
              <h1 className="mb-6 text-2xl font-semibold">Shopping Cart</h1>

              {/* Table Header - Hidden on mobile */}
              <div className="border-cart-border text-muted-foreground mb-4 hidden gap-4 border-b pb-4 text-sm font-medium lg:grid lg:grid-cols-[2fr,1fr,1fr,auto]">
                <div>Product</div>
                <div className="text-center">Quantity</div>
                <div className="text-center">Price</div>
                <div className="w-8"></div>
              </div>

              {/* Cart Items */}
              <div className="space-y-4">
                {cartItems.map((item) => (
                  <CartItem
                    key={item.id}
                    {...item}
                    onUpdateQuantity={updateQuantity}
                    onRemove={removeItem}
                  />
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex flex-col gap-4 sm:flex-row">
              <Button variant="outline" className="flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
              <Button variant="destructive" className="bg-destructive hover:bg-destructive/90">
                Cancel Order
              </Button>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            <CouponSection onApplyCoupon={handleApplyCoupon} />
            <OrderSummary subtotal={subtotal} discount={discount} delivery={delivery} tax={tax} />
            <PaymentMethods />
          </div>
        </div>
      </div>
    </div>
  );
}
