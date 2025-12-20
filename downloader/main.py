import tkinter as tk
import traceback
import sys
import os

def main():
    root = tk.Tk()
    from app import Pica
    Pica(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Silent fail for users
        try:
            # optional: log for you (not user)
            base = os.path.join(os.path.expanduser("~"), ".pica")
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, "error.log"), "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass

        # exit silently
        sys.exit(0)
