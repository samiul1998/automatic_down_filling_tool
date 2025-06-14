from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

class BottomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFont(QFont("Courier New", 12))
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def setup(self, data_rows, cols):
        """Initialize the table structure"""
        total_rows = 2 + (2 * data_rows) + 2  # Headers + data + totals
        total_cols = cols + 1  # 3 fixed columns + size columns
        self.setRowCount(total_rows)
        self.setColumnCount(total_cols)
        self.clear_spans()
        self.setup_headers(total_cols)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        
        # Set column widths
        self.setColumnWidth(0, 200)   # panel name
        self.setColumnWidth(1, 120)   # panel qty
        self.setColumnWidth(2, 150)   # weight column
        for col in range(3, total_cols):
            self.setColumnWidth(col, 100)  # size columns
            
    def clear_spans(self):
        """Clear all existing spans in the table"""
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                if self.columnSpan(row, col) > 1 or self.rowSpan(row, col) > 1:
                    self.setSpan(row, col, 1, 1)
                    
    def setup_headers(self, total_cols):
        """Set up the header structure for the table"""
        # Set up header merges
        self.setSpan(0, 0, 2, 1)  # PANEL NAME (span 2 rows)
        self.setSpan(0, 1, 2, 1)  # PANEL QTY (span 2 rows)
        self.setSpan(0, 2, 2, 1)  # WEIGHT (span 2 rows)
        self.setSpan(0, 3, 1, total_cols - 3)  # SIZE header span
        
        # Create and set header items
        headers = [
            ("PANEL NAME", 0, 0),
            ("PANEL QTY", 0, 1),
            ("WEIGHT", 0, 2),
            ("SIZE || WEIGHT DISTRIBUTION", 0, 3)
        ]
        
        for text, row, col in headers:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row, col, item)
            
    def update_data(self, top_table, ecodown_weight, garment_weight, base_size):
        """Update the table data based on top table and input weights"""
        # Clear previous highlights
        self.clear_highlights()
        
        # Get base size column
        base_col_top = self.get_base_size_col(top_table, base_size)
        
        # Calculate total sewing area for base size
        total_base_area = self.calculate_total_base_area(top_table, base_col_top)
        
        # Update each panel's data
        for top_row in range(2, top_table.rowCount() - 1):
            self.update_panel_data(top_table, top_row, ecodown_weight, 
                                  garment_weight, base_col_top, total_base_area)
            
        # Auto-resize weight column
        self.resize_weight_column()
        
        # Update totals
        self.update_totals()
        
    def clear_highlights(self):
        """Clear all previous highlights in the table"""
        for row in range(self.rowCount()):
            for col in range(3, self.columnCount()):  # Skip first 3 cols
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setBold(False)
                    item.setFont(font)
                    item.setForeground(QColor(0, 0, 0))  # Reset to black
                    
    def get_base_size_col(self, top_table, base_size):
        """Get the column index for the base size"""
        if not base_size:
            return None
            
        for col in range(2, top_table.columnCount()):
            item = top_table.item(1, col)
            if item and item.text().strip() == base_size:
                return col
        return None
        
    def calculate_total_base_area(self, top_table, base_col):
        """Calculate total sewing area for the base size"""
        if base_col is None:
            return 0.0
            
        total_area = 0.0
        for row in range(2, top_table.rowCount() - 1):
            qty_item = top_table.item(row, 1)
            area_item = top_table.item(row, base_col)
            try:
                qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 1
                area = float(area_item.text()) if area_item and area_item.text() else 0.0
                total_area += qty * area
            except:
                continue
        return total_area
        
    def update_panel_data(self, top_table, top_row, ecodown_weight, 
                         garment_weight, base_col_top, total_base_area):
        """Update data for a single panel"""
        bottom_row = 2 + ((top_row - 2) * 2)
        
        # Get panel info from top table
        name_item = top_table.item(top_row, 0)
        qty_item = top_table.item(top_row, 1)
        
        # Check if panel is valid
        try:
            panel_qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 0
        except:
            panel_qty = 0
            
        is_valid_panel = panel_qty > 0
        show_garment_label = is_valid_panel and garment_weight > 0
        
        # Set panel name
        name_cell = self.item(bottom_row, 0)
        if not name_cell:
            name_cell = QTableWidgetItem()
            name_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name_cell.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(bottom_row, 0, name_cell)
        name_cell.setText(name_item.text() if name_item and is_valid_panel else "")
        self.setSpan(bottom_row, 0, 2, 1)
        self.setRowHidden(bottom_row, not is_valid_panel)
        self.setRowHidden(bottom_row + 1, not show_garment_label)
        
        # Set panel quantity
        qty_cell = self.item(bottom_row, 1)
        if not qty_cell:
            qty_cell = QTableWidgetItem()
            qty_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_cell.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(bottom_row, 1, qty_cell)
        qty_cell.setText(f"1X{panel_qty}" if panel_qty > 0 else "")
        self.setSpan(bottom_row, 1, 2, 1)
        
        # Set weight labels
        self.set_weight_labels(bottom_row, is_valid_panel, show_garment_label)
        
        # Skip if panel is invalid
        if not is_valid_panel:
            self.clear_panel_data(bottom_row)
            return
            
        # Update size columns
        if base_col_top is not None and total_base_area > 0:
            self.update_size_columns(top_table, top_row, bottom_row, ecodown_weight, 
                                    garment_weight, base_col_top, total_base_area, panel_qty)
        else:
            self.clear_size_columns(bottom_row)
            
    def set_weight_labels(self, bottom_row, is_valid_panel, show_garment_label):
        """Set the weight labels for a panel"""
        down_label_cell = self.item(bottom_row, 2)
        if not down_label_cell:
            down_label_cell = QTableWidgetItem("DOWN WEIGHT")
            down_label_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            down_label_cell.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(bottom_row, 2, down_label_cell)
        else:
            down_label_cell.setText("DOWN WEIGHT" if is_valid_panel else "")
            
        garment_label_cell = self.item(bottom_row + 1, 2)
        if not garment_label_cell:
            garment_label_cell = QTableWidgetItem("GARMENTS WEIGHT")
            garment_label_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            garment_label_cell.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(bottom_row + 1, 2, garment_label_cell)
        else:
            garment_label_cell.setText("GARMENTS WEIGHT" if show_garment_label else "")
            
    def clear_panel_data(self, bottom_row):
        """Clear data for an invalid panel"""
        for col in range(3, self.columnCount()):
            down_cell = self.item(bottom_row, col)
            if not down_cell:
                down_cell = QTableWidgetItem()
                down_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                down_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                self.setItem(bottom_row, col, down_cell)
            down_cell.setText("")
            
            garment_cell = self.item(bottom_row + 1, col)
            if garment_cell:
                garment_cell.setText("")
                
    def update_size_columns(self, top_table, top_row, bottom_row, ecodown_weight, 
                           garment_weight, base_col_top, total_base_area, panel_qty):
        """Update the size columns for a valid panel"""
        base_area_item = top_table.item(top_row, base_col_top)
        try:
            base_area = float(base_area_item.text()) if base_area_item and base_area_item.text() else 0.0
            base_sewing_area = panel_qty * base_area
        except:
            base_sewing_area = 0.0
            
        for col in range(3, self.columnCount()):
            top_col = col - 1
            if top_col >= top_table.columnCount():
                continue
                
            area_item = top_table.item(top_row, top_col)
            try:
                size_area = float(area_item.text()) if area_item and area_item.text() else 0.0
                sewing_area = panel_qty * size_area
            except:
                sewing_area = 0.0
                
            if base_sewing_area > 0:
                down_weight_val = (ecodown_weight / total_base_area) * sewing_area
                garment_weight_val = (garment_weight / total_base_area) * sewing_area
                
                if panel_qty > 0:
                    down_weight_val /= panel_qty
                    garment_weight_val /= panel_qty
            else:
                down_weight_val = 0.0
                garment_weight_val = 0.0
                
            # Set down weight
            down_cell = self.item(bottom_row, col)
            if not down_cell:
                down_cell = QTableWidgetItem()
                down_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                down_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                self.setItem(bottom_row, col, down_cell)
            down_cell.setText(f"{down_weight_val:.2f}" if down_weight_val != 0 else "")
            
            # Set garment weight
            if garment_weight > 0:
                garment_cell = self.item(bottom_row + 1, col)
                if not garment_cell:
                    garment_cell = QTableWidgetItem()
                    garment_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    garment_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.setItem(bottom_row + 1, col, garment_cell)
                garment_cell.setText(f"{garment_weight_val:.2f}" if garment_weight_val != 0 else "")
            else:
                garment_cell = self.item(bottom_row + 1, col)
                if garment_cell:
                    garment_cell.setText("")
                    
            # Highlight base size column
            if top_col == base_col_top:
                self.highlight_base_size_cell(down_cell)
                if garment_cell:
                    self.highlight_base_size_cell(garment_cell)
                    
    def highlight_base_size_cell(self, item):
        """Highlight a cell as the base size"""
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setForeground(QColor(0, 0, 255))  # Blue
        
    def clear_size_columns(self, bottom_row):
        """Clear size columns when no valid base size"""
        for col in range(3, self.columnCount()):
            down_cell = self.item(bottom_row, col)
            if not down_cell:
                down_cell = QTableWidgetItem()
                down_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                down_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                self.setItem(bottom_row, col, down_cell)
            down_cell.setText("")
            
            garment_cell = self.item(bottom_row + 1, col)
            if garment_cell:
                garment_cell.setText("")
                
    def resize_weight_column(self):
        """Resize the weight column to fit content"""
        self.resizeColumnToContents(2)
        font_metrics = self.fontMetrics()
        min_width = max(
            font_metrics.horizontalAdvance("DOWN WEIGHT"),
            font_metrics.horizontalAdvance("GARMENTS WEIGHT")
        ) + 20
        if self.columnWidth(2) < min_width:
            self.setColumnWidth(2, min_width)
            
    def update_totals(self):
        """Calculate and display totals"""
        total_rows = self.rowCount()
        total_cols = self.columnCount()
        
        down_totals = [0.0] * (total_cols - 3)
        garment_totals = [0.0] * (total_cols - 3)
        
        # Calculate totals
        for row in range(2, total_rows - 2, 2):
            qty_item = self.item(row, 1)
            try:
                qty = int(qty_item.text().replace("1X", "")) if qty_item and qty_item.text().startswith("1X") else 1
            except:
                qty = 1
                
            for i, col in enumerate(range(3, total_cols)):
                down_cell = self.item(row, col)
                try:
                    down_val = float(down_cell.text()) if down_cell and down_cell.text() else 0.0
                    down_totals[i] += down_val * qty
                except:
                    pass
                    
                garment_row = row + 1
                if not self.isRowHidden(garment_row):
                    garment_cell = self.item(garment_row, col)
                    try:
                        g_val = float(garment_cell.text()) if garment_cell and garment_cell.text() else 0.0
                        garment_totals[i] += g_val * qty
                    except:
                        pass
                        
        # Display totals
        self.display_totals(down_totals, garment_totals)
        
    def display_totals(self, down_totals, garment_totals):
        """Display the calculated totals in the table"""
        total_rows = self.rowCount()
        total_cols = self.columnCount()
        
        # TOTAL DOWN WEIGHT row
        total_row = total_rows - 2
        self.setSpan(total_row, 0, 1, 3)
        self.setRowHidden(total_row, False)
        label_item = QTableWidgetItem("TOTAL DOWN WEIGHT")
        label_item.setFlags(Qt.ItemFlag.NoItemFlags)
        label_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        label_item.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        self.setItem(total_row, 0, label_item)
        
        for i, col in enumerate(range(3, total_cols)):
            item = QTableWidgetItem(f"{round(down_totals[i]):.0f}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(total_row, col, item)
            
        # GARMENT TOTAL row
        total_row = total_rows - 1
        self.setSpan(total_row, 0, 1, 3)
        show_garments_total = any(garment_totals)  # Only show if there are values
        self.setRowHidden(total_row, not show_garments_total)
        
        if show_garments_total:
            label_item = QTableWidgetItem("TOTAL GARMENT WEIGHT")
            label_item.setFlags(Qt.ItemFlag.NoItemFlags)
            label_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            label_item.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
            self.setItem(total_row, 0, label_item)
            
            for i, col in enumerate(range(3, total_cols)):
                item = QTableWidgetItem(f"{round(garment_totals[i]):.0f}")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(total_row, col, item)