import sys
import os
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, 
                               QFileDialog, QLabel, QSplitter)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, QObject, Slot, Qt, QFileInfo

# Ensure app module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.processor import CityGMLProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CityGMLViewer")

class WebBridge(QObject):
    """
    Bridge between Python and JavaScript.
    """
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback

    @Slot(str)
    def onObjectClicked(self, object_id):
        """Called from JS when an object is clicked."""
        logger.info(f"Clicked Object ID: {object_id}")
        self.update_callback(object_id)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("High-Performance CityGML Viewer (M3)")
        self.resize(1200, 800)
        
        # Processor integration
        self.processor = CityGMLProcessor()
        self.current_metadata = {}
        self.current_glb_path = None

        # internal server for local files? 
        # For QWebEngineView, we can use file:// protocol if CORS allows, 
        # or we might need to enable settings.
        
        self.setup_ui()

    def setup_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter to resize sidebar
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Sidebar (Left) ---
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # Controls
        self.btn_load = QPushButton("Load CityGML")
        self.btn_load.clicked.connect(self.load_citygml)
        sidebar_layout.addWidget(self.btn_load)

        self.lbl_status = QLabel("Ready")
        sidebar_layout.addWidget(self.lbl_status)
        
        # Attribute Inspector
        self.tree_info = QTreeWidget()
        self.tree_info.setHeaderLabels(["Attribute", "Value"])
        sidebar_layout.addWidget(self.tree_info)
        
        splitter.addWidget(sidebar_widget)

        # --- 3D View (Right) ---
        # WebEngine setup
        self.webview = QWebEngineView()
        
        # Enable settings for local file access and hardware acceleration
        settings = self.webview.settings()
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True) # Important for loading models
        
        # Setup Bridge
        self.bridge = WebBridge(self.update_attribute_panel)
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.bridge)
        self.webview.page().setWebChannel(self.channel)
        
        # Load index.html
        html_path = os.path.abspath(os.path.join("resources", "web", "index.html"))
        if not os.path.exists(html_path):
             logger.error(f"index.html not found at {html_path}")
             self.lbl_status.setText("Error: index.html missing")
        else:
             self.webview.setUrl(QUrl.fromLocalFile(html_path))
        
        splitter.addWidget(self.webview)
        
        # Set initial splitter sizes (30% sidebar, 70% map)
        splitter.setSizes([300, 900])

    def load_citygml(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CityGML Data", "", "CityGML/JSON (*.gml *.xml *.json *.city.json)")
        if not file_path:
            return

        self.lbl_status.setText(f"Processing {os.path.basename(file_path)}...")
        QApplication.processEvents() # Force UI update

        try:
            # 1. Process File
            glb_path, metadata = self.processor.process_file(file_path)
            self.current_metadata = metadata
            self.current_glb_path = glb_path
            
            # 2. visual path needs to be proper for JS
            # Note: For MacOS local files in WebEngine, usually 'file://' works.
            # But converting local path to file URL properly is safer
            
            # Ensure path is absolute
            abs_glb_path = os.path.abspath(glb_path)
            
            # HACK: WebEngine sometimes blocks loading local files from file:// scheme due to security.
            # If CORS issues arise, we might need a custom scheme handler or disable web security.
            # For this boilerplate, we assume allow params in setup_ui handle it.
            
            # Pass to JS
            # We call the JS function `loadModel(path)`
            # We must escape backslashes on Windows, but this is Mac.
            
            js_code = f"loadModel('file://{abs_glb_path}');"
            logger.info(f"Executing JS: {js_code}")
            self.webview.page().runJavaScript(js_code)
            
            self.lbl_status.setText(f"Loaded: {len(metadata)} objects")

        except Exception as e:
            logger.error(f"Error loading file: {e}")
            self.lbl_status.setText(f"Error: {e}")

    def update_attribute_panel(self, object_id):
        """
        Updates the QTreeWidget with attributes for the given object ID.
        """
        self.tree_info.clear()
        
        if object_id not in self.current_metadata:
            item = QTreeWidgetItem(["ID", str(object_id)])
            self.tree_info.addTopLevelItem(item)
            item = QTreeWidgetItem(["Status", "No Metadata Found"])
            self.tree_info.addTopLevelItem(item)
            return

        attributes = self.current_metadata[object_id]
        
        # Recursively add items
        self.add_tree_items(self.tree_info.invisibleRootItem(), attributes)
        self.tree_info.expandAll()

    def add_tree_items(self, parent_item, data):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem([str(key), ""])
                parent_item.addChild(item)
                self.add_tree_items(item, value)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem([f"[{i}]", ""])
                parent_item.addChild(item)
                self.add_tree_items(item, value)
        else:
            # Leaf node
            # If the parent created the item with empty value, set it now.
            # A bit tricky with the recursive structure, usually easier to set value on creation.
            # Here, since we created the item with [key, ""], we validly access column 1.
            parent_item.setText(1, str(data))

if __name__ == "__main__":
    # Fix for some M1/M2/M3 OpenGL issues in Qt
    # os.environ["QT_API"] = "pyside6" 
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
