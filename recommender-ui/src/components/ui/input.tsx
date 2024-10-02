import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export interface FlexibleInputProps
  extends Omit<React.InputHTMLAttributes<HTMLDivElement>, "onChange"> {
  onChange?: (value: string) => void;
  minRows?: number;
  maxRows?: number;
}

export interface FlexibleInputRef {
  focus: () => void;
  blur: () => void;
  setContent: (content: string) => void;
}

const FlexibleInput = React.forwardRef<FlexibleInputRef, FlexibleInputProps>(
  (
    { className, minRows = 1, maxRows = 5, onChange, onKeyDown, ...props },
    ref
  ) => {
    const [content, setContent] = React.useState("");
    const divRef = React.useRef<HTMLDivElement>(null);

    React.useImperativeHandle(ref, () => ({
      focus: () => divRef.current?.focus(),
      blur: () => divRef.current?.blur(),
      setContent: (newContent: string) => {
        setContent(newContent);
        if (divRef.current) {
          divRef.current.textContent = newContent;
        }
      },
    }));

    const adjustHeight = React.useCallback(() => {
      const div = divRef.current;
      if (div) {
        div.style.height = "auto";
        const lineHeight = parseInt(window.getComputedStyle(div).lineHeight);
        const minHeight = minRows * lineHeight;
        const maxHeight = maxRows * lineHeight;
        const scrollHeight = div.scrollHeight;

        div.style.height = `${Math.min(
          Math.max(minHeight, scrollHeight),
          maxHeight
        )}px`;
      }
    }, [minRows, maxRows]);

    React.useEffect(() => {
      adjustHeight();
    }, [content, adjustHeight]);

    const handleInput = (e: React.FormEvent<HTMLDivElement>) => {
      const value = e.currentTarget.textContent || "";
      setContent(value);
      onChange?.(value);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onKeyDown?.(e as any);
      }
    };

    return (
      <div
        ref={divRef}
        contentEditable
        className={cn(
          "flex min-h-[36px] w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 overflow-auto",
          className
        )}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        {...props}
      />
    );
  }
);
FlexibleInput.displayName = "FlexibleInput";

export { Input, FlexibleInput };
