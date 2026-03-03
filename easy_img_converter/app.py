try:
    from easy_img_converter.ui.main_window import MainWindow
except ModuleNotFoundError:
    # Allow running `python app.py` from inside the `easy_img_converter` folder.
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from easy_img_converter.ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
