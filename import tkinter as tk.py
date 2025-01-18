import os
import sys
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Collaborative Drawing App")
        self.root.geometry("800x600")

        # Get the correct path for the preset folder
        if getattr(sys, 'frozen', False):  # If the app is frozen (exe)
            self.preset_folder = os.path.join(sys._MEIPASS, "preset_images")
        else:
            self.preset_folder = "preset_images"
        
        os.makedirs(self.preset_folder, exist_ok=True)  # Ensure the folder exists

        # Create a Toolbar for tools
        self.toolbar = tk.Frame(self.root, bg="lightgray", height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Initialize current tool and settings
        self.current_tool = "marker1"
        self.tools = {
            "marker1": {"type": "line", "color": "red", "width": 2},
            "marker2": {"type": "line", "color": "blue", "width": 4},
            "circle": {"type": "shape", "color": "green", "size": 30},
        }

        # Add buttons to the toolbar
        self.create_tool_button("Marker Type 1", "marker1")
        self.create_tool_button("Marker Type 2", "marker2")
        self.create_tool_button("Draw Circle", "circle")

        # Add a dropdown for preset images
        self.preset_images = self.get_preset_images()
        self.selected_preset = tk.StringVar(value="Select Preset Image")
        self.preset_menu = tk.OptionMenu(self.toolbar, self.selected_preset, *self.preset_images, command=self.load_preset_image)
        self.preset_menu.pack(side=tk.LEFT, padx=5, pady=5)

        # Create the Canvas
        self.canvas = tk.Canvas(self.root, bg="white", width=800, height=500)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Set up drawing
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)

        # Add menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Load Image", command=self.load_image)
        file_menu.add_command(label="Clear Canvas", command=self.clear_canvas)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Variables to store image and drawing data
        self.original_image = None  # Original image for scaling
        self.image_on_canvas = None  # Current canvas image
        self.image_width = 0
        self.image_height = 0
        self.drawing_data = []  # Store drawings as [(type, *coords, color, width/size)]

        # Disable window resizing
        self.root.resizable(False, False)

    def get_preset_images(self):
        """Get a list of image files from the preset folder."""
        valid_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
        return [f for f in os.listdir(self.preset_folder) if os.path.splitext(f)[1].lower() in valid_extensions]

    def load_preset_image(self, image_name):
        """Load a preset image onto the canvas."""
        file_path = os.path.join(self.preset_folder, image_name)
        if os.path.exists(file_path):
            self.load_image(file_path)

    def create_tool_button(self, label, tool_key):
        """Create a button on the toolbar to select a tool."""
        button = tk.Button(self.toolbar, text=label, command=lambda: self.select_tool(tool_key))
        button.pack(side=tk.LEFT, padx=5, pady=5)

    def select_tool(self, tool_key):
        """Select a tool by setting the current tool."""
        if tool_key in self.tools:
            self.current_tool = tool_key
            print(f"Selected tool: {tool_key}")

    def start_draw(self, event):
        """Start drawing or place a shape."""
        tool_settings = self.tools.get(self.current_tool, {})
        if tool_settings.get("type") == "shape":
            self.draw_shape(event)
        elif tool_settings.get("type") == "line":
            self.last_x, self.last_y = event.x, event.y

            # Store the start position for line drawing
            self.drawing_data.append(("line", self.last_x, self.last_y, None, None, tool_settings["color"], tool_settings["width"]))

    def draw(self, event):
        """Draw a line from the last position to the current position."""
        tool_settings = self.tools.get(self.current_tool, {})
        if tool_settings.get("type") == "line" and self.last_x is not None and self.last_y is not None:
            x, y = event.x, event.y
            color = tool_settings["color"]
            width = tool_settings["width"]

            # Draw the line on the canvas
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill=color, width=width)

            # Update drawing data with new line position
            self.drawing_data[-1] = ("line", self.last_x, self.last_y, x, y, color, width)

            # Update last_x, last_y for the next line segment
            self.last_x, self.last_y = x, y

    def draw_shape(self, event):
        """Draw a predefined shape at the clicked location."""
        tool_settings = self.tools[self.current_tool]
        color = tool_settings["color"]
        size = tool_settings["size"]

        x1 = event.x - size // 2
        y1 = event.y - size // 2
        x2 = event.x + size // 2
        y2 = event.y + size // 2

        # Draw the shape on the canvas
        self.canvas.create_oval(x1, y1, x2, y2, outline=color, fill=color)

        # Store the shape data
        self.drawing_data.append(("shape", x1, y1, x2, y2, color, size))

    def load_image(self, file_path=None):
        """Load an image onto the canvas."""
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            try:
                # Load the image
                self.original_image = Image.open(file_path)
                self.image_width, self.image_height = self.original_image.size
                self.resize_image()  # Trigger resizing and drawing
            except Exception as e:
                print(f"Error loading image: {e}")

    def resize_image(self):
        """Resize the image to fit the canvas and draw it."""
        if self.original_image:
            # Get the canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Maintain aspect ratio for resizing
            image_ratio = self.image_width / self.image_height
            canvas_ratio = canvas_width / canvas_height

            if image_ratio > canvas_ratio:
                # Fit to canvas width
                new_width = canvas_width
                new_height = int(canvas_width / image_ratio)
            else:
                # Fit to canvas height
                new_height = canvas_height
                new_width = int(canvas_height * image_ratio)

            # Resize the image
            resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.image_on_canvas = ImageTk.PhotoImage(resized_image)

            # Calculate offsets for centering
            self.image_x_offset = (canvas_width - new_width) / 2
            self.image_y_offset = (canvas_height - new_height) / 2

            # Clear the canvas and redraw the image
            self.canvas.delete("all")
            self.canvas.create_image(self.image_x_offset, self.image_y_offset, anchor=tk.NW, image=self.image_on_canvas)

            # Redraw all existing drawings
            self.redraw_drawings()

    def redraw_drawings(self):
        """Redraw all stored drawings on the canvas."""
        for drawing in self.drawing_data:
            if drawing[0] == "line":
                x1, y1, x2, y2, color, width = drawing[1], drawing[2], drawing[3], drawing[4], drawing[5], drawing[6]
                if x2 is not None and y2 is not None:
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            elif drawing[0] == "shape":
                x1, y1, x2, y2, color, size = drawing[1], drawing[2], drawing[3], drawing[4], drawing[5], drawing[6]
                self.canvas.create_oval(x1, y1, x2, y2, outline=color, fill=color)

    def clear_canvas(self):
        """Clear all drawings from the canvas."""
        self.canvas.delete("all")
        self.drawing_data.clear()


def main():
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
