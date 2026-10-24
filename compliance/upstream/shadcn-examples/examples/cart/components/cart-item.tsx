import { Button } from "@/components/ui/button";
import { Minus, Plus, Trash2 } from "lucide-react";

interface CartItemProps {
  id: string;
  name: string;
  color: string;
  price: number;
  quantity: number;
  image: string;
  onUpdateQuantity: (id: string, quantity: number) => void;
  onRemove: (id: string) => void;
}

export const CartItem = ({
  id,
  name,
  color,
  price,
  quantity,
  image,
  onUpdateQuantity,
  onRemove
}: CartItemProps) => {
  return (
    <div className="bg-cart-item border-cart-border flex items-center gap-4 rounded-lg border p-4">
      {/* Product Image */}
      <div className="bg-muted flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-lg">
        <img src={image} alt={name} className="h-full w-full rounded-lg object-cover" />
      </div>

      {/* Product Details */}
      <div className="min-w-0 flex-1">
        <h3 className="text-foreground line-clamp-2 text-sm font-medium lg:text-base">{name}</h3>
        <p className="text-cart-color mt-1 text-sm">
          Color: <span>{color}</span>
        </p>
      </div>

      {/* Quantity Controls */}
      <div className="bg-cart-quantity flex items-center gap-2 rounded-lg p-1">
        <Button
          variant="ghost"
          size="icon"
          className="hover:bg-muted h-8 w-8"
          onClick={() => onUpdateQuantity(id, Math.max(1, quantity - 1))}>
          <Minus className="h-4 w-4" />
        </Button>
        <span className="min-w-[2rem] text-center text-sm font-medium">{quantity}</span>
        <Button
          variant="ghost"
          size="icon"
          className="hover:bg-muted h-8 w-8"
          onClick={() => onUpdateQuantity(id, quantity + 1)}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Price */}
      <div className="text-cart-price min-w-[80px] text-right text-sm font-semibold lg:text-base">
        ${price.toFixed(2)}
      </div>

      {/* Remove Button */}
      <Button
        variant="ghost"
        size="icon"
        className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 h-8 w-8"
        onClick={() => onRemove(id)}>
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
};
