# Application entry point: run this file to start the project.
from gui.main_window import DeadmanApp

if __name__ == "__main__":
    # Create the main window and keep the GUI running until the user closes it.
    DeadmanApp().mainloop()
