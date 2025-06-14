import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton,
                             QDialog, QListWidget, QDialogButtonBox, QFormLayout,
                             QFrame, QSizePolicy, QStyleFactory, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, 
                             QMessageBox, QProgressBar)
from PyQt6.QtGui import QFont, QDoubleValidator, QPalette, QColor, QIntValidator, QKeyEvent, QIcon, QPixmap
from PyQt6.QtCore import Qt, QDate, QSettings, QEvent, QTimer, QCoreApplication, QPoint, QTimer, QPropertyAnimation, QEasingCurve
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from ui.dialogs.factory_edit_dialog import FactoryEditDialog
from ui.dialogs.confirmation_dialog import ConfirmationDialog
from ui.dialogs.progress_dialog import ProgressDialog
from ui.tables.top_table_widget import TableWidget
from ui.tables.table_item_delegate import TableItemDelegate, UpperCaseItemDelegate
from ui.utils.upper_case_line_edit import UpperCaseLineEdit
from ui.tables.bottom_table_widget import BottomTableWidget

class DownAllocationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuration variables
        self.input_field_width = 250
        self.vertical_spacing = 12
        self.horizontal_spacing = 20
        self.factory_font_size = 15
        self.input_fields_font_size = 20 #Input fields font size
        self.input_fields_label_size = 20 # Input fields label size
        self.row_column_count_size = 12  # Row height for count size
        self.button_font_size = 12 #Button font size
        self.top_table_font_size = 12
        self.table_font_size = 12
        self.default_data_rows = 10  # Just the editable data rows
        self.default_cols = 10       # Total columns (2 fixed + size columns)
        self.input_field_height = 10  # New variable for consistent input field height
        self.horizontal_form_spacing = 30  # New variable for horizontal spacing in form

        self.top_fixed_header = None
        self.bottom_fixed_header = None
        self.top_scroll_table = None
        self.bottom_scroll_table = None

        # Calculate total rows needed (headers + data + total)
        self.default_total_rows = 2 + self.default_data_rows + 1

        # Column width settings
        self.panel_name_col_width = 200
        self.panel_qty_col_width = 120
        self.sewing_area_col_width = 100

        self.base_font = QFont("Courier New", self.row_column_count_size)
        
        # Initialize UI
        self.init_ui()

        # Connect change trackers for reset all fields
        self.connect_change_trackers()

        # Check if factory info exists
        self.settings = QSettings("DownAllocation", "FactoryInfo")
        factory_name = self.settings.value("factory_name", "")
        factory_location = self.settings.value("factory_location", "")

        if not factory_name or not factory_location:
            self.show_factory_edit()
        else:
            self.update_factory_display(factory_name, factory_location)

    def init_ui(self):
        self.setWindowTitle("Automatic Down Allocation System")
        self.setMinimumSize(1300, 900)
        self.setFont(self.base_font)
        
        #icon
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'app_icon.ico')
        icon_path = os.path.abspath(icon_path)
        self.setWindowIcon(QIcon(icon_path))

        self.showMaximized()

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(self.vertical_spacing)

        # Factory display section
        self.factory_display_frame = QFrame()
        self.factory_display_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        factory_layout = QHBoxLayout(self.factory_display_frame)
        factory_layout.setContentsMargins(0, 0, 0, 0)

        # Factory info labels
        self.factory_info_layout = QVBoxLayout()
        self.factory_info_layout.setSpacing(2)
        self.factory_info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.factory_name_label = QLabel()
        self.factory_name_label.setFont(
            QFont("Courier New", self.factory_font_size, QFont.Weight.Bold))
        self.factory_name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.factory_location_label = QLabel()
        self.factory_location_label.setFont(
            QFont("Courier New", self.factory_font_size))
        self.factory_location_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.factory_info_layout.addWidget(self.factory_name_label)
        self.factory_info_layout.addWidget(self.factory_location_label)
        factory_layout.addLayout(self.factory_info_layout, stretch=1)

        # Edit button
        self.edit_factory_btn = QPushButton("Edit")
        self.edit_factory_btn.setFont(
            QFont("Courier New", self.button_font_size))
        self.edit_factory_btn.setFixedSize(80, 30)
        self.edit_factory_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.edit_factory_btn.clicked.connect(self.show_factory_edit)
        factory_layout.addWidget(
            self.edit_factory_btn, 0, Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.factory_display_frame)

        # Input form section
        form_card = QFrame()
        form_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
            }}
            QLabel {{
                font-family: "Courier New";
                font-size: {self.input_fields_label_size}px;
                color: #495057;
                padding-right: 5px;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                font-family: "Courier New";
                font-size: {self.input_fields_font_size}px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                min-height: {self.input_field_height}px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left-width: 1px;
                border-left-color: #e0e0e0;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
            QComboBox QAbstractItemView {{
                font-family: "Courier New";
                font-size: {self.input_fields_font_size}px;
                border: 1px solid #e0e0e0;
                selection-background-color: #e3f2fd;
                selection-color: black;
                padding: 4px;
            }}
        """)

        # Create container widget for centering
        form_container = QWidget()
        form_container_layout = QHBoxLayout(form_container)
        form_container_layout.setContentsMargins(0, 0, 0, 0)

        # Create 3 columns for the form
        form_columns = QHBoxLayout()
        form_columns.setSpacing(20)

        # Column 1: Date, Buyer, Style
        col1 = QVBoxLayout()
        col1.setSpacing(self.vertical_spacing)

        # Date input
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                Qt.AlignmentFlag.AlignVCenter)
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(self.input_field_width)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        col1.addLayout(date_layout)

        # Buyer input
        buyer_layout = QHBoxLayout()
        buyer_label = QLabel("Buyer:")
        buyer_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                 Qt.AlignmentFlag.AlignVCenter)
        self.buyer_input = UpperCaseLineEdit()
        self.buyer_input.setFixedWidth(self.input_field_width)
        buyer_layout.addWidget(buyer_label)
        buyer_layout.addWidget(self.buyer_input)
        col1.addLayout(buyer_layout)

        # Style input
        style_layout = QHBoxLayout()
        style_label = QLabel("Style:")
        style_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                 Qt.AlignmentFlag.AlignVCenter)
        self.style_input = UpperCaseLineEdit()
        self.style_input.setFixedWidth(self.input_field_width)
        style_layout.addWidget(style_label)
        style_layout.addWidget(self.style_input)
        col1.addLayout(style_layout)

        form_columns.addLayout(col1)

        # Column 2: Season, Garments Stage, Base Size
        col2 = QVBoxLayout()
        col2.setSpacing(self.vertical_spacing)

        # Season dropdown
        season_layout = QHBoxLayout()
        season_label = QLabel("Season:")
        season_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                  Qt.AlignmentFlag.AlignVCenter)
        self.season_combo = QComboBox()
        self.season_combo.setFixedWidth(self.input_field_width)
        self.season_combo.addItems(["", "SS", "AW", "SP", "FW"])
        season_layout.addWidget(season_label)
        season_layout.addWidget(self.season_combo)
        col2.addLayout(season_layout)

        # Garments Stage dropdown
        garments_layout = QHBoxLayout()
        garments_label = QLabel("Garments Stage:")
        garments_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.garments_stage_combo = QComboBox()
        self.garments_stage_combo.setFixedWidth(self.input_field_width)
        self.garments_stage_combo.addItems([
            "", "SIZE SET", "P TEST SAMPLE", "FIT SAMPLE", "PP SAMPLE",
            "DEVELOPMENT", "PHOTO SAMPLE", "SHIPMENT SAMPLE", "BULK", "SMS SAMPLE"
        ])
        garments_layout.addWidget(garments_label)
        garments_layout.addWidget(self.garments_stage_combo)
        col2.addLayout(garments_layout)

        # Base Size dropdown
        base_layout = QHBoxLayout()
        base_label = QLabel("Base Size:")
        base_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                Qt.AlignmentFlag.AlignVCenter)
        self.base_size_combo = QComboBox()
        self.base_size_combo.setFixedWidth(self.input_field_width)
        self.base_size_combo.currentTextChanged.connect(
            self.highlight_base_size)
        base_layout.addWidget(base_label)
        base_layout.addWidget(self.base_size_combo)
        col2.addLayout(base_layout)

        form_columns.addLayout(col2)

        # Column 3: Ecodown Weight, Garments Weight, Approx Weight
        col3 = QVBoxLayout()
        col3.setSpacing(self.vertical_spacing)

        # Ecodown Fibers Weight
        ecodown_layout = QHBoxLayout()
        ecodown_label = QLabel("Ecodown Weight:")
        ecodown_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.ecodown_input = UpperCaseLineEdit()
        self.ecodown_input.setPlaceholderText("0")
        self.ecodown_input.setValidator(QDoubleValidator(0, 9999, 2))
        self.ecodown_input.setFixedWidth(self.input_field_width)
        ecodown_layout.addWidget(ecodown_label)
        ecodown_layout.addWidget(self.ecodown_input)
        col3.addLayout(ecodown_layout)

        # Garments Weight
        garment_layout = QHBoxLayout()
        garment_label = QLabel("Garments Weight:")
        garment_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.garment_weight_input = UpperCaseLineEdit()
        self.garment_weight_input.setPlaceholderText("0")
        self.garment_weight_input.setValidator(QDoubleValidator(0, 9999, 2))
        self.garment_weight_input.setFixedWidth(self.input_field_width)
        garment_layout.addWidget(garment_label)
        garment_layout.addWidget(self.garment_weight_input)
        col3.addLayout(garment_layout)

        # Approximate Weight
        approx_layout = QHBoxLayout()
        approx_label = QLabel("Approx Weight:")
        approx_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                  Qt.AlignmentFlag.AlignVCenter)
        self.approx_weight_input = UpperCaseLineEdit()
        self.approx_weight_input.setPlaceholderText("0")
        self.approx_weight_input.setValidator(QDoubleValidator(0, 9999, 2))
        self.approx_weight_input.setFixedWidth(self.input_field_width)
        approx_layout.addWidget(approx_label)
        approx_layout.addWidget(self.approx_weight_input)
        col3.addLayout(approx_layout)

        form_columns.addLayout(col3)

        # Add the form columns to container with centering
        form_container_layout.addStretch()
        form_container_layout.addLayout(form_columns)
        form_container_layout.addStretch()

        # Set layout to form card
        form_card.setLayout(QHBoxLayout())
        form_card.layout().addWidget(form_container)
        form_card.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(form_card)

        # Table section
        table_container = QFrame()
        table_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table_layout = QVBoxLayout(table_container)

        # SET ROW/COLUMN button section
        self.row_col_frame = QFrame()
        row_col_layout = QHBoxLayout(self.row_col_frame)
        row_col_layout.setContentsMargins(0, 0, 0, 10)

        # Row input - shows just the data rows count
        self.row_input = QLineEdit(str(self.default_data_rows))
        self.row_input.setValidator(QIntValidator(1, 100))
        self.row_input.setFixedWidth(60)
        self.row_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Column input - shows just the size columns count (excluding first 2 columns)
        self.col_input = QLineEdit(str(self.default_cols - 2))
        self.col_input.setValidator(QIntValidator(1, 50))
        self.col_input.setFixedWidth(60)
        self.col_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set button
        self.set_row_col_btn = QPushButton("SET PANEL | SIZE")
        self.set_row_col_btn.setFont(
            QFont("Courier New", self.button_font_size, QFont.Weight.Bold))
        self.set_row_col_btn.setFixedHeight(35)
        self.set_row_col_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.set_row_col_btn.clicked.connect(self.set_table_dimensions)

         # Reset button
        self.reset_btn = QPushButton("RESET")
        self.reset_btn.setFont(
            QFont("Courier New", self.button_font_size, QFont.Weight.Bold))
        self.reset_btn.setFixedHeight(35)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.reset_btn.setEnabled(False)  # Disabled by default
        self.reset_btn.clicked.connect(self.reset_table)

        row_col_layout.addStretch()
        row_col_layout.addWidget(QLabel("PANEL:"))
        row_col_layout.addWidget(self.row_input)
        row_col_layout.addWidget(QLabel("SIZE:"))
        row_col_layout.addWidget(self.col_input)
        row_col_layout.addWidget(self.set_row_col_btn)
        row_col_layout.addWidget(self.reset_btn)
        table_layout.addWidget(self.row_col_frame)

        # Create top table (renamed from self.top_table to self.top_table)
        self.top_table = TableWidget(self.default_total_rows, self.default_cols)
        self.top_table.setFont(QFont("Courier New", self.top_table_font_size))
        self.setup_table()  # This will setup the top table
        table_layout.addWidget(self.top_table)

        # Add bottom table
        self.bottom_table = BottomTableWidget(self)
        self.bottom_table.setFont(QFont("Courier New", self.top_table_font_size))
        self.setup_bottom_table()

         # Hide in production (PyInstaller)
        if getattr(sys, 'frozen', False):
            self.bottom_table.setVisible(False)
        table_layout.addWidget(self.bottom_table)
        
        main_layout.addWidget(table_container)

        # Set modern style
        fusion_style = QStyleFactory.create("Fusion")
        if fusion_style:
            self.setStyle(fusion_style)

        # Custom palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase,
                         QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(227, 242, 253))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

    def connect_change_trackers(self):
        """Connect all input fields to track changes"""
        # Form fields
        self.date_input.dateChanged.connect(self.enable_reset_button)
        self.buyer_input.textChanged.connect(self.enable_reset_button)
        self.style_input.textChanged.connect(self.enable_reset_button)
        self.season_combo.currentTextChanged.connect(self.enable_reset_button)
        self.garments_stage_combo.currentTextChanged.connect(self.enable_reset_button)
        self.ecodown_input.textChanged.connect(self.enable_reset_button)
        self.garment_weight_input.textChanged.connect(self.enable_reset_button)
        self.approx_weight_input.textChanged.connect(self.enable_reset_button)
        self.base_size_combo.currentTextChanged.connect(self.enable_reset_button)
        
        # Connect signals for real-time updates
        self.top_table.itemChanged.connect(self.update_bottom_table)
        self.ecodown_input.textChanged.connect(self.update_bottom_table)
        self.garment_weight_input.textChanged.connect(self.update_bottom_table)
        self.base_size_combo.currentTextChanged.connect(self.update_bottom_table)

    def enable_reset_button(self):
        """Enable the reset button when called"""
        self.reset_btn.setEnabled(True)

    def setup_table(self):
        # Calculate total rows needed (headers + data + total)
        total_rows = 2 + self.default_data_rows + 1

        # Set table dimensions
        self.top_table.setRowCount(total_rows)
        self.top_table.setColumnCount(self.default_cols)

        # Change all self.top_table references to self.top_table
        for row in range(self.top_table.rowCount()):
            for col in range(self.top_table.columnCount()):
                if self.top_table.columnSpan(row, col) > 1 or self.top_table.rowSpan(row, col) > 1:
                    self.top_table.setSpan(row, col, 1, 1)

        # Set up header merges
        self.top_table.setSpan(0, 0, 2, 1)  # PANEL NAME (span 2 rows)
        self.top_table.setSpan(0, 1, 2, 1)  # PANEL QUANTITY (span 2 rows)
        self.top_table.setSpan(0, 2, 1, self.default_cols - 2)  # SIZE header span

        # Create and set header items
        headers = [
            ("PANEL NAME", 0, 0),
            ("PANEL QUANTITY", 0, 1),
            ("SIZE || PANEL SEWING AREA", 0, 2)
        ]

        for text, row, col in headers:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFont(
                QFont("Courier New", self.top_table_font_size, QFont.Weight.Bold))
            # Make completely non-interactive
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.top_table.setItem(row, col, item)

        # Set size headers in row 1 (below merged SIZE header)
        for col in range(2, self.default_cols):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFont(QFont("Courier New", self.top_table_font_size))
            item.setToolTip("Enter size name like XS, S, M, L")
            # Make size headers fully editable
            item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                          Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            self.top_table.setItem(1, col, item)
            self.top_table.itemChanged.connect(self.format_size_headers)

        # Set up data rows (from row 2 to second-to-last row)
        for row in range(2, total_rows - 1):
            # Panel Name column
            name_item = QTableWidgetItem()
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_table.setItem(row, 0, name_item)

            # Panel Quantity column
            qty_item = QTableWidgetItem()
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_table.setItem(row, 1, qty_item)

            # Sewing area columns
            for col in range(2, self.default_cols):
                area_item = QTableWidgetItem()
                area_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.top_table.setItem(row, col, area_item)

        # Set up TOTAL row
        total_item = QTableWidgetItem("TOTAL")
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        total_item.setFont(
            QFont("Courier New", self.top_table_font_size, QFont.Weight.Bold))
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                            Qt.ItemFlag.ItemIsSelectable)  # Not editable
        self.top_table.setItem(total_rows - 1, 0, total_item)
        self.top_table.setSpan(total_rows - 1, 0, 1, 2)

        for col in range(2, self.default_cols):
            total_cell = QTableWidgetItem("0.00")
            total_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_cell.setFont(
                QFont("Courier New", self.top_table_font_size, QFont.Weight.Bold))
            total_cell.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                Qt.ItemFlag.ItemIsSelectable)  # Not editable
            self.top_table.setItem(total_rows - 1, col, total_cell)

        # Configure table appearance
        self.top_table.horizontalHeader().setVisible(False)
        self.top_table.verticalHeader().setVisible(False)
        self.top_table.setShowGrid(True)

        # Set column widths
        self.top_table.setColumnWidth(0, self.panel_name_col_width)
        self.top_table.setColumnWidth(1, self.panel_qty_col_width)
        for col in range(2, self.default_cols):
            self.top_table.setColumnWidth(col, self.sewing_area_col_width)

        # Set up item delegates for validation and formatting
        self.top_table.setItemDelegate(UpperCaseItemDelegate(self.top_table))  # First for real-time uppercase
        self.top_table.setItemDelegate(TableItemDelegate(self.top_table))      # Second for validation

        # Connect signals
        self.top_table.itemChanged.connect(self.update_table)
        self.top_table.itemChanged.connect(self.format_table_text)

        # Update base size dropdown
        self.update_base_size_dropdown()
        
    def setup_bottom_table(self):
        """Set up the bottom table structure"""
        self.bottom_table.setup(self.default_data_rows, self.default_cols - 2)
        
        # Set size headers by copying from top table
        for col in range(3, self.bottom_table.columnCount()):
            top_col = col - 1  # Adjust for extra weight column
            if top_col < self.top_table.columnCount():
                size_item = self.top_table.item(1, top_col)
                if size_item:
                    item = QTableWidgetItem(size_item.text())
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFont(QFont("Courier New", self.table_font_size))
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.bottom_table.setItem(1, col, item)
        
        # Initialize data
        self.update_bottom_table()

    def update_bottom_table(self):
        """Update the bottom table data"""
        try:
            ecodown_weight = float(self.ecodown_input.text()) if self.ecodown_input.text() else 0.0
        except:
            ecodown_weight = 0.0
            
        try:
            garment_weight = float(self.garment_weight_input.text()) if self.garment_weight_input.text() else 0.0
        except:
            garment_weight = 0.0
            
        base_size = self.base_size_combo.currentText()
        
        self.bottom_table.update_data(
            self.top_table, 
            ecodown_weight, 
            garment_weight, 
            base_size
        )

    def format_table_text(self, item):
        # Only convert for Panel Name (column 0) and Size Name (row 1, columns ≥2)
        if (item.column() == 0 and item.row() >= 2) or (item.row() == 1 and item.column() >= 2):
            text = item.text()
            if text and not text.isupper():
                self.top_table.blockSignals(True)
                item.setText(text.upper())
                self.top_table.blockSignals(False)
                if item.row() == 1:  # If size header changed
                    self.update_base_size_dropdown()

    def format_size_headers(self, item):
        if item.row() == 1 and item.column() >= 2:  # Only for size headers
            text = item.text()
            if text:
                # Block signals to prevent recursive calls
                self.top_table.blockSignals(True)
                item.setText(text.upper())
                self.top_table.blockSignals(False)
                self.update_base_size_dropdown()  # Update dropdown if sizes changed

    def set_table_dimensions(self):
        try:
            new_data_rows = int(self.row_input.text())
            new_size_cols = int(self.col_input.text())

            if new_data_rows < 1 or new_size_cols < 1:
                return

            # Show progress dialog
            progress = ProgressDialog(
                "Resizing Table", "Preparing table adjustment...", self)
            progress.show()
            QApplication.processEvents()
            progress.update_progress(5)

            # Save existing data
            saved_data = self.save_table_data()
            progress.update_progress(20)

            # Update dimensions
            self.default_data_rows = new_data_rows
            self.default_cols = new_size_cols + 2

            # Rebuild both tables
            self.setup_table()
            self.setup_bottom_table()
            progress.update_progress(80)

            # Restore data
            self.restore_table_data(saved_data)
            progress.update_progress(95)

            # Update calculations
            self.calculate_totals()
            self.update_bottom_table()
            progress.update_progress(100)

        except ValueError as e:
            QMessageBox.warning(self, "Input Error",
                                "Please enter valid numbers for rows and columns")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def save_table_data(self):
        """Save all table data before expansion"""
        saved_data = {
            'size_names': [],
            'panel_names': [],
            'panel_qtys': [],
            'sewing_areas': []
        }

        # Save size names (row 1, columns 2+)
        for col in range(2, self.top_table.columnCount()):
            item = self.top_table.item(1, col)
            saved_data['size_names'].append(item.text() if item else "")

        # Save panel names and quantities (rows 2+)
        for row in range(2, self.top_table.rowCount() - 1):  # Exclude TOTAL row
            name_item = self.top_table.item(row, 0)
            qty_item = self.top_table.item(row, 1)
            saved_data['panel_names'].append(
                name_item.text() if name_item else "")
            saved_data['panel_qtys'].append(
                qty_item.text() if qty_item else "")

        # Save sewing area data (rows 2+, columns 2+)
        for row in range(2, self.top_table.rowCount() - 1):
            row_data = []
            for col in range(2, self.top_table.columnCount()):
                item = self.top_table.item(row, col)
                row_data.append(item.text() if item else "")
            saved_data['sewing_areas'].append(row_data)

        return saved_data

    def restore_table_data(self, saved_data):
        """Restore table data after expansion"""
        # Restore size names
        for col in range(2, min(self.top_table.columnCount(), len(saved_data['size_names']) + 2)):
            if col - 2 < len(saved_data['size_names']):
                item = self.top_table.item(1, col)
                if item:
                    item.setText(saved_data['size_names'][col - 2])

        # Restore panel names and quantities
        for row in range(2, min(2 + self.default_data_rows, len(saved_data['panel_names']) + 2)):
            if row - 2 < len(saved_data['panel_names']):
                name_item = self.top_table.item(row, 0)
                if name_item:
                    name_item.setText(saved_data['panel_names'][row - 2])

                qty_item = self.top_table.item(row, 1)
                if qty_item:
                    qty_item.setText(saved_data['panel_qtys'][row - 2])

        # Restore sewing area data
        for row in range(2, min(2 + self.default_data_rows, len(saved_data['sewing_areas']) + 2)):
            if row - 2 < len(saved_data['sewing_areas']):
                for col in range(2, min(self.top_table.columnCount(), len(saved_data['sewing_areas'][row - 2]) + 2)):
                    if col - 2 < len(saved_data['sewing_areas'][row - 2]):
                        item = self.top_table.item(row, col)
                        if item:
                            item.setText(saved_data['sewing_areas'][row - 2][col - 2])

    def update_table(self, item):
        # Save state for undo/redo
        self.top_table.push_undo_state()

        # Update base size dropdown when size names change
        if item.row() == 1 and item.column() >= 2:
            self.update_base_size_dropdown()
            self.setup_bottom_table()  # Rebuild bottom table when sizes change

        # Check for duplicates
        if item.row() == 1 and item.column() >= 2:
            current_text = item.text().strip()
            if current_text:
                for col in range(2, self.top_table.columnCount()):
                    if col != item.column():
                        other_item = self.top_table.item(1, col)
                        if other_item and other_item.text().strip() == current_text:
                            QMessageBox.warning(self, "Duplicate Size",
                                                f"Size '{current_text}' already exists!")
                            item.setText("")
                            break

            # If user deleted a size that was selected as base size, reset selection
            current_base = self.base_size_combo.currentText()
            if current_base and current_base not in self.get_available_sizes():
                self.base_size_combo.setCurrentIndex(0)
                self.highlight_base_size("")

        # Calculate totals when data changes
        if (item.column() == 1 and item.row() >= 2) or (item.column() >= 2 and item.row() >= 2 and item.row() < self.top_table.rowCount() - 1):
            self.calculate_totals()
            self.update_bottom_table()  # Update bottom table when data changes

    def get_available_sizes(self):
        return [self.top_table.item(1, col).text().strip()
                for col in range(2, self.top_table.columnCount())
                if self.top_table.item(1, col) and self.top_table.item(1, col).text().strip()]

    def highlight_base_size(self, size):
        try:
            # Clear previous highlights in bottom_table only
            for row in range(self.bottom_table.rowCount()):
                for col in range(3, self.bottom_table.columnCount()):  # Skip first 3 cols
                    item = self.bottom_table.item(row, col)
                    if item:
                        font = item.font()
                        font.setBold(False)
                        item.setFont(font)
                        item.setForeground(QColor(0, 0, 0))  # Black

            # Highlight selected base size in bottom_table only
            if size and str(size).strip():
                size = str(size).strip()
                for col in range(3, self.bottom_table.columnCount()):
                    header_item = self.bottom_table.item(1, col)
                    if header_item and header_item.text().strip() == size:
                        # Apply bold + blue to entire column
                        for row in range(2, self.bottom_table.rowCount()):
                            item = self.bottom_table.item(row, col)
                            if item:
                                font = item.font()
                                font.setBold(True)
                                item.setFont(font)
                                item.setForeground(QColor(0, 0, 255))  # Blue
                        break
        except Exception as e:
            print(f"Error highlighting base size: {str(e)}")

    def update_base_size_dropdown(self):
        try:
            # Block signals temporarily to prevent recursive calls
            self.base_size_combo.blockSignals(True)

            sizes = []
            # Collect sizes in the order they appear in the table (left to right)
            for col in range(2, self.top_table.columnCount()):
                size_item = self.top_table.item(1, col)
                if size_item and (size_text := size_item.text().strip()):
                    if size_text not in sizes:  # Avoid duplicates while preserving order
                        sizes.append(size_text)

            current_selection = self.base_size_combo.currentText()
            self.base_size_combo.clear()
            self.base_size_combo.addItems(
                [""] + sizes)  # Add empty option first

            # Restore selection if it still exists
            if current_selection in sizes:
                self.base_size_combo.setCurrentText(current_selection)
            else:
                self.base_size_combo.setCurrentIndex(0)

        except Exception as e:
            print(f"Error updating base size dropdown: {str(e)}")
            QMessageBox.warning(
                self, "Error", "Failed to update size dropdown")
        finally:
            self.base_size_combo.blockSignals(False)

    def calculate_totals(self):
        # Top table totals
        for col in range(2, self.top_table.columnCount()):
            total = 0.0
            for row in range(2, self.top_table.rowCount() - 1):
                # Get quantity value
                qty_item = self.top_table.item(row, 1)
                try:
                    qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() and 1 <= int(qty_item.text()) <= 9 else 1
                except:
                    qty = 1

                # Get sewing area value
                area_item = self.top_table.item(row, col)
                try:
                    area = float(area_item.text()) if area_item and area_item.text().replace(".", "", 1).isdigit() else 0.0
                except:
                    area = 0.0

                total += qty * area

            # Update total cell
            total_item = self.top_table.item(self.top_table.rowCount() - 1, col)
            if total_item:
                total_item.setText(f"{total:.2f}")

        # Update bottom table
        self.update_bottom_table()

    def reset_table(self):
        confirm = ConfirmationDialog(
            "Confirm Reset",
            "This will reset all table data and settings to defaults.\nAre you sure you want to continue?",
            self
        )
        
        result = confirm.exec()
        
        if result == QDialog.DialogCode.Accepted:
            try:
                # Show progress dialog
                progress = ProgressDialog("Resetting Table", "Clearing table data...", self)
                progress.show()
                QApplication.processEvents()
                progress.update_progress(10)

                # Store factory info
                factory_name = self.factory_name_label.text()
                factory_location = self.factory_location_label.text()
                progress.update_progress(20)

                # Clear table
                for row in range(self.top_table.rowCount()):
                    for col in range(self.top_table.columnCount()):
                        if row == 0:  # Skip headers
                            continue
                        item = self.top_table.item(row, col)
                        if item:
                            item.setText("")
                    
                    if row % 10 == 0:
                        progress_val = 20 + 30 * row / self.top_table.rowCount()
                        progress.update_progress(int(progress_val))
                        QApplication.processEvents()

                progress.update_progress(50)

                # Reset dimensions
                self.default_data_rows = 10
                self.default_cols = 10
                self.row_input.setText(str(self.default_data_rows))
                self.col_input.setText(str(self.default_cols - 2))
                progress.update_progress(60)

                # Rebuild table
                self.setup_table()
                progress.update_progress(80)

                # Reset form fields
                self.date_input.setDate(QDate.currentDate())
                self.season_combo.setCurrentIndex(0)
                self.ecodown_input.clear()
                self.buyer_input.clear()
                self.garments_stage_combo.setCurrentIndex(0)
                self.garment_weight_input.clear()
                self.style_input.clear()
                self.base_size_combo.clear()
                self.approx_weight_input.clear()
                progress.update_progress(90)

                # Restore factory info
                self.update_factory_display(factory_name, factory_location)
                progress.update_progress(100)

                # Disable reset button after successful reset
                self.reset_btn.setEnabled(False)

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Reset failed: {str(e)}")
        elif result == QDialog.DialogCode.Rejected:
            # User clicked No or closed the dialog
            pass

    def clear_table(self):
        # Clear all data but keep structure
        for row in range(self.top_table.rowCount()):
            for col in range(self.top_table.columnCount()):
                if row == 0:  # Main headers
                    continue
                elif row == 1 and col >= 2:  # Size headers
                    item = self.top_table.item(row, col)
                    if item:
                        item.setText("")
                elif row == self.top_table.rowCount() - 1:  # Total row
                    if col == 0:
                        continue
                    elif col >= 2:
                        item = self.top_table.item(row, col)
                        if item:
                            item.setText("0.00")
                else:  # Data rows
                    item = self.top_table.item(row, col)
                    if item:
                        item.setText("")

        # Reset base size dropdown
        self.base_size_combo.clear()

        # Recalculate totals
        self.calculate_totals()

    def show_factory_edit(self):
        current_name = self.settings.value("factory_name", "")
        current_location = self.settings.value("factory_location", "")

        dialog = FactoryEditDialog(current_name, current_location, self)
        
        # Center the dialog relative to main window
        dialog_rect = dialog.geometry()
        main_rect = self.geometry()
        dialog.move(
            main_rect.center().x() - dialog_rect.width() // 2,
            main_rect.center().y() - dialog_rect.height() // 2
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            factory_name, factory_location = dialog.get_factory_info()
            self.settings.setValue("factory_name", factory_name)
            self.settings.setValue("factory_location", factory_location)
            self.update_factory_display(factory_name, factory_location)

    def update_factory_display(self, name, location):
        self.factory_name_label.setText(name)
        self.factory_location_label.setText(location)
        self.setWindowTitle(f"Automatic Down Allocation System - {name}")