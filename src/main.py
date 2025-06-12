from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton,
                             QDialog, QListWidget, QDialogButtonBox, QFormLayout,
                             QFrame, QSizePolicy, QStyleFactory, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QStyledItemDelegate,
                             QMessageBox, QProgressBar)
from PyQt6.QtGui import QFont, QDoubleValidator, QPalette, QColor, QIntValidator, QKeyEvent, QIcon, QPixmap
from PyQt6.QtCore import Qt, QDate, QSettings, QEvent, QTimer, QCoreApplication, QPoint, QTimer, QPropertyAnimation, QEasingCurve
import sys
import os
from splash_screen import SplashScreen
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



class FactoryEditDialog(QDialog):
    def __init__(self, current_name="", current_location="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Factory Information")
        self.setFixedSize(500, 200)

        # Set font for entire dialog
        self.setFont(QFont("Courier New", parent.label_font_size))

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Form layout for factory inputs
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.factory_name_input = QLineEdit(current_name)
        self.factory_name_input.setFont(
            QFont("Courier New", parent.label_font_size))
        self.factory_location_input = QLineEdit(current_location)
        self.factory_location_input.setFont(
            QFont("Courier New", parent.label_font_size))

        form_layout.addRow(QLabel("Factory Name:"), self.factory_name_input)
        form_layout.addRow(QLabel("Factory Location:"),
                           self.factory_location_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_inputs)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_inputs(self):
        if self.factory_name_input.text().strip() and self.factory_location_input.text().strip():
            self.accept()
        else:
            self.factory_name_input.setFocus()

    def get_factory_info(self):
        return (self.factory_name_input.text().strip(),
                self.factory_location_input.text().strip())


class TableItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        # Don't create editor for main header row (0) or total row
        if index.row() == 0 or index.row() == self.parent().rowCount() - 1:
            return None
        # Always allow editing for size headers (row 1, columns 2+)
        if index.row() == 1 and index.column() >= 2:
            editor = super().createEditor(parent, option, index)
            return editor
        # For data rows (row 2+)
        if index.row() >= 2 and index.row() < self.parent().rowCount() - 1:
            editor = super().createEditor(parent, option, index)
            # Set validation based on column
            if index.column() == 1:  # Panel Quantity column (1-9)
                validator = QIntValidator(1, 9, parent)
                editor.setValidator(validator)
            elif index.column() >= 2:  # Sewing area columns
                validator = QDoubleValidator(0, 9999, 2, parent)
                validator.setNotation(
                    QDoubleValidator.Notation.StandardNotation)
                editor.setValidator(validator)
            return editor
        return None

    def eventFilter(self, editor, event):
        # Intercept key press in editor
        if isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right,
                               Qt.Key.Key_Up, Qt.Key.Key_Down):
                # Commit data before navigating
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor, QStyledItemDelegate.EndEditHint.NoHint)
                # Return True to consume the event
                return True
        return super().eventFilter(editor, event)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Set text alignment to center for all cells
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        # Show hint text for empty cells with gray color
        if not index.data(Qt.ItemDataRole.DisplayRole):
            option.palette.setColor(
                QPalette.ColorRole.Text, QColor(150, 150, 150))
            if index.row() == 1 and index.column() >= 2:  # Size headers
                option.text = f"SIZE {index.column()-1}"
            elif index.row() >= 2 and index.row() < self.parent().rowCount() - 1:
                if index.column() == 0:  # Panel Name
                    option.text = "PANEL NAME"
                elif index.column() == 1:  # Panel Quantity
                    option.text = "0"
                elif index.column() >= 2:  # Sewing area
                    option.text = "0.00"


class TableWidget(QTableWidget):
    def __init__(self, rows, cols, parent=None):
        super().__init__(rows, cols, parent)
        self.setup_table()
        self.pasted_cells = []
        self.undo_stack = []
        self.redo_stack = []
        self.initial_state_saved = False  # Track if initial state is saved
        self.programmatic_change = False  # Flag to prevent undo tracking during restore
        self._updating_table = False
        self._updating_bottom_table = False

    def setup_table(self):
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked |
                             QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Connect itemChanged signal to track user changes
        self.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        """Track when user manually changes items"""
        if not self.programmatic_change:
            # Save initial state if this is the first user change
            if not self.initial_state_saved:
                # Save the state before this change by temporarily reverting
                current_text = item.text()
                self.programmatic_change = True
                item.setText("")  # Temporarily clear to save previous state
                self.push_undo_state()
                item.setText(current_text)  # Restore current text
                self.programmatic_change = False
                self.initial_state_saved = True
            
            # Apply uppercase conversion for specific cells
            row, col = item.row(), item.column()
            if col == 0 or (row == 1 and col >= 2):
                if item.text() != item.text().upper():
                    self.programmatic_change = True
                    item.setText(item.text().upper())
                    self.programmatic_change = False

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_selection()
        elif event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.push_undo_state()
            self.paste_to_selection()
            self.select_pasted_cells()
        elif event.key() == Qt.Key.Key_Delete:
            self.push_undo_state()
            self.clear_selection()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_F2):
            current = self.currentIndex()
            if current.isValid() and current.row() < self.rowCount() - 1:
                self.edit(current)
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.redo()
            else:
                self.undo()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.redo()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.redo()
        elif event.key() in range(Qt.Key.Key_0, Qt.Key.Key_9 + 1):
            current = self.currentIndex()
            if current.isValid() and current.row() < self.rowCount() - 1:
                if event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                    self.edit(current)
                    if self.cellWidget(current.row(), current.column()):
                        self.cellWidget(
                            current.row(), current.column()).keyPressEvent(event)
                    return
            super().keyPressEvent(event)
        elif event.text() and not event.modifiers():
            current = self.currentIndex()
            if current.isValid() and current.row() < self.rowCount() - 1:
                self.edit(current)
                if self.cellWidget(current.row(), current.column()):
                    self.cellWidget(current.row(), current.column()
                                    ).keyPressEvent(event)
                return
            super().keyPressEvent(event)
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            current = self.currentIndex()
            if current.isValid():
                if self.state() == QAbstractItemView.State.EditingState:
                    self.commitData(self.cellWidget(
                        current.row(), current.column()))
                    self.closePersistentEditor(
                        self.item(current.row(), current.column()))

                row, col = current.row(), current.column()
                if event.key() == Qt.Key.Key_Up:
                    row -= 1
                elif event.key() == Qt.Key.Key_Down:
                    row += 1
                elif event.key() == Qt.Key.Key_Left:
                    col -= 1
                elif event.key() == Qt.Key.Key_Right:
                    col += 1

                new_index = self.model().index(row, col)
                if new_index.isValid() and row < self.rowCount():
                    self.setCurrentIndex(new_index)
                    self.scrollTo(new_index)
                return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def save_state(self):
        state = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            state.append(row_data)
        return state

    def push_undo_state(self):
        """Only save undo state when there are actual user changes"""
        if self.programmatic_change:
            return
            
        current_state = self.save_state()
        
        # Don't save duplicate states
        if self.undo_stack and current_state == self.undo_stack[-1]:
            return
            
        self.undo_stack.append(current_state)
        self.redo_stack = []  # Clear redo stack when new action is performed
        
        # Limit undo stack size
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
            
        # Save current state to redo stack
        current_state = self.save_state()
        self.redo_stack.append(current_state)
        
        # Get and restore previous state
        previous_state = self.undo_stack.pop()
        self.restore_state(previous_state)
        
        # Limit redo stack size
        if len(self.redo_stack) > 100:
            self.redo_stack.pop(0)

    def redo(self):
        if not self.redo_stack:
            return
            
        # Save current state to undo stack
        current_state = self.save_state()
        self.undo_stack.append(current_state)
        
        # Get and restore next state
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)
        
        # Limit undo stack size
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def restore_state(self, state):
        """Restore table state without triggering undo tracking"""
        self.programmatic_change = True
        self.blockSignals(True)
        
        try:
            for row in range(min(self.rowCount(), len(state))):
                for col in range(min(self.columnCount(), len(state[row]))):
                    item = self.item(row, col)
                    if not item:
                        item = QTableWidgetItem()
                        self.setItem(row, col, item)
                    item.setText(state[row][col])
        finally:
            self.blockSignals(False)
            self.programmatic_change = False
            self.viewport().update()
            
            # Recalculate totals if main window has the method
            main_window = self.window()
            if hasattr(main_window, 'calculate_totals'):
                main_window.calculate_totals()

    def copy_selection(self):
        selection = self.selectedIndexes()
        if not selection:
            return
        rows = sorted(index.row() for index in selection)
        cols = sorted(index.column() for index in selection)
        min_row, max_row = rows[0], rows[-1]
        min_col, max_col = cols[0], cols[-1]
        clipboard = QApplication.clipboard()
        text = ""
        for r in range(min_row, max_row + 1):
            row_text = []
            for c in range(min_col, max_col + 1):
                item = self.item(r, c)
                row_text.append(item.text() if item else "")
            text += "\t".join(row_text) + "\n"
        clipboard.setText(text.strip())

    def paste_to_selection(self):
        try:
            # Show progress dialog immediately
            progress = ProgressDialog("Pasting Data", "Processing paste operation...", self)
            progress.show()
            QApplication.processEvents()
            progress.update_progress(5)

            # Get selection and clipboard data (10-15% progress)
            selection = self.selectedIndexes()
            if not selection:
                progress.close()
                return

            first_row = selection[0].row()
            first_col = selection[0].column()
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            
            if not text.strip():
                progress.close()
                return

            rows = [row for row in text.split('\n') if row.strip()]
            grid = [row.split('\t') for row in rows]
            progress.update_progress(15)

            # Check if we're pasting into size headers (15-20% progress)
            is_size_header_paste = (first_row == 1)
            if is_size_header_paste:
                is_vertical = all(len(row) == 1 for row in grid) and len(grid) > 1
                if is_vertical:
                    transposed = []
                    for i in range(len(grid[0])):
                        row_data = []
                        for j in range(len(grid)):
                            if i < len(grid[j]):
                                row_data.append(grid[j][i])
                            else:
                                row_data.append('')
                        transposed.append(row_data)
                    grid = transposed
            progress.update_progress(20)

            # Calculate needed dimensions (20-25% progress)
            main_window = self.window()
            needed_rows = len(grid)
            needed_cols = max(len(row) for row in grid)
            current_editable_rows = self.rowCount() - 3
            current_editable_cols = self.columnCount() - 2

            rows_to_add = max(0, (first_row + needed_rows) - (current_editable_rows + 2))
            cols_to_add = max(0, (first_col + needed_cols) - (current_editable_cols + 2))
            progress.update_progress(25)

            # Expand table if needed (25-50% progress)
            if rows_to_add > 0 or cols_to_add > 0:
                progress.label.setText("Adjusting table size...")
                
                if hasattr(main_window, 'default_data_rows'):
                    main_window.default_data_rows += rows_to_add
                if hasattr(main_window, 'default_cols'):
                    main_window.default_cols += cols_to_add
                
                # Save existing data before expansion (30-40% progress)
                if hasattr(main_window, 'save_table_data'):
                    saved_data = main_window.save_table_data()
                progress.update_progress(40)
                
                # Rebuild table with new dimensions (40-45% progress)
                if hasattr(main_window, 'setup_table'):
                    main_window.setup_table()
                progress.update_progress(45)
                
                # Restore data after expansion (45-50% progress)
                if hasattr(main_window, 'restore_table_data'):
                    main_window.restore_table_data(saved_data)
                
                if hasattr(main_window, 'row_input'):
                    main_window.row_input.setText(str(main_window.default_data_rows))
                if hasattr(main_window, 'col_input'):
                    main_window.col_input.setText(str(main_window.default_cols - 2))
            
            progress.update_progress(50)
            progress.label.setText("Pasting data...")

            # Process paste operation (50-90% progress)
            self.pasted_cells = []
            total_cells = len(grid) * max(len(row) for row in grid) if grid else 1
            processed_cells = 0
            
            # Set programmatic flag to prevent undo tracking during paste
            self.programmatic_change = True
            
            try:
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        current_row = first_row + r
                        current_col = first_col + c

                        # Update progress every 10 cells
                        processed_cells += 1
                        if processed_cells % 10 == 0:
                            progress_val = 50 + (40 * processed_cells / total_cells)
                            progress.update_progress(min(90, int(progress_val)))
                            QApplication.processEvents()

                        if (current_row >= self.rowCount() or 
                            current_col >= self.columnCount() or
                            current_row == 0 or 
                            current_row == self.rowCount() - 1):
                            continue

                        # Apply validation rules
                        if current_row != 1:  # Not size header
                            if current_col == 1:  # Panel Quantity column
                                if not value.isdigit() or not (1 <= int(value) <= 9):
                                    continue
                            elif current_col >= 2:  # Sewing area
                                try:
                                    float(value)
                                except ValueError:
                                    continue

                        # Create item if needed
                        if not self.item(current_row, current_col):
                            self.setItem(current_row, current_col, QTableWidgetItem())

                        # Set text with uppercase conversion where needed
                        if current_col == 0 or (current_row == 1 and current_col >= 2):
                            self.item(current_row, current_col).setText(value.strip().upper())
                        else:
                            self.item(current_row, current_col).setText(value.strip())
                        
                        self.pasted_cells.append((current_row, current_col))
            finally:
                self.programmatic_change = False

            # Final updates (90-100% progress)
            progress.update_progress(95)
            self.select_pasted_cells()
            
            if hasattr(main_window, 'calculate_totals'):
                main_window.calculate_totals()
            
            progress.update_progress(100)

        except Exception as e:
            QMessageBox.warning(self, "Paste Error", f"Failed to paste data: {str(e)}")
            if 'progress' in locals():
                progress.close()

    def select_pasted_cells(self):
        if not self.pasted_cells:
            return
        self.clearSelection()
        for row, col in self.pasted_cells:
            item = self.item(row, col)
            if item:
                item.setSelected(True)

    def clear_selection(self):
        for index in self.selectedIndexes():
            if index.row() == 0 or index.row() == self.rowCount() - 1:
                continue
            if self.item(index.row(), index.column()):
                self.item(index.row(), index.column()).setText("")

class UpperCaseLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("font-family: 'Courier New';")
        self.textChanged.connect(self.force_uppercase)

    def force_uppercase(self, text):
        if text != text.upper():
            cursor_pos = self.cursorPosition()
            self.blockSignals(True)
            self.setText(text.upper())
            self.setCursorPosition(cursor_pos)
            self.blockSignals(False)

    def keyPressEvent(self, event: QKeyEvent):
        if event.text():
            upper_char = event.text().upper()
            modified_event = QKeyEvent(
                event.type(),
                event.key(),
                event.modifiers(),
                upper_char
            )
            super().keyPressEvent(modified_event)
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text().upper())


class UpperCaseItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        # Apply to Panel Name column (column 0) and Size Headers (row 1, columns ≥2)
        if index.column() == 0 or (index.row() == 1 and index.column() >= 2):
            editor = UpperCaseLineEdit(parent)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, UpperCaseLineEdit):
            editor.blockSignals(True)
            editor.setText(index.data(Qt.ItemDataRole.DisplayRole) or "")
            editor.blockSignals(False)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, UpperCaseLineEdit):
            model.setData(index, editor.text().strip().upper(),
                          Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def eventFilter(self, editor, event):
        if isinstance(editor, UpperCaseLineEdit):
            if event.type() == QEvent.Type.KeyPress:
                if event.text():
                    editor.keyPressEvent(event)
                    self.commitData.emit(editor)
                    return True
            elif event.type() == QEvent.Type.FocusOut:
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor, QStyledItemDelegate.EndEditHint.NoHint)
                return True
        return super().eventFilter(editor, event)


class ProgressDialog(QDialog):
    def __init__(self, title="Processing", message="Please wait...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)
        
        # Timer for smooth progress animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.increment_progress)
        self.current_progress = 0
        self.target_progress = 0
        self.step = 1
        
    def increment_progress(self):
        if self.current_progress < self.target_progress:
            self.current_progress += self.step
            self.progress.setValue(self.current_progress)
            QApplication.processEvents()
        else:
            self.timer.stop()
            if self.current_progress >= 100:
                self.close()
    
    def update_progress(self, value):
        self.target_progress = value
        self.step = max(1, (self.target_progress - self.current_progress) // 10)
        self.timer.start(30)  # Update every 30ms for smooth animation
    
    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

class ConfirmationDialog(QDialog):
    def __init__(self, title="Confirm Action", message="Are you sure you want to proceed?", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)  # Enable close button
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Message label
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI';
                font-size: 14px;
                color: #333;
                padding: 20px;
            }
        """)
        layout.addWidget(self.label)
        
        # Button box
        button_box = QDialogButtonBox()
        button_box.setCenterButtons(True)
        
        self.yes_btn = button_box.addButton("Yes", QDialogButtonBox.ButtonRole.AcceptRole)
        self.no_btn = button_box.addButton("No", QDialogButtonBox.ButtonRole.RejectRole)
        
        # Connect buttons
        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)
        
        # Styling for buttons
        button_style = """
            QPushButton {
                font-family: 'Segoe UI';
                font-size: 13px;
                min-width: 80px;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton[text="Yes"] {
                background-color: #4285F4;
                color: white;
            }
            QPushButton[text="Yes"]:hover {
                background-color: #3367D6;
            }
            QPushButton[text="No"] {
                background-color: #F1F3F4;
                color: #3C4043;
            }
            QPushButton[text="No"]:hover {
                background-color: #E8EAED;
            }
        """
        button_box.setStyleSheet(button_style)
        
        layout.addWidget(button_box)
        
        # Dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
        """)

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
        self.bottom_table = QTableWidget()
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
        # Calculate rows needed (2 header rows + 2 rows per data row + 2 total rows)
        data_rows = self.default_data_rows
        total_rows = 2 + (2 * data_rows) + 2  # Headers + data + totals
        # Columns match top table but with extra "WEIGHT" column
        total_cols = self.default_cols + 1
        self.bottom_table.setRowCount(total_rows)
        self.bottom_table.setColumnCount(total_cols)

        # Clear all spans first
        for row in range(self.bottom_table.rowCount()):
            for col in range(self.bottom_table.columnCount()):
                if self.bottom_table.columnSpan(row, col) > 1 or self.bottom_table.rowSpan(row, col) > 1:
                    self.bottom_table.setSpan(row, col, 1, 1)

        # Set up header merges (rows 0-1 are headers)
        self.bottom_table.setSpan(0, 0, 2, 1)  # PANEL NAME (span 2 rows)
        self.bottom_table.setSpan(0, 1, 2, 1)  # PANEL QTY (span 2 rows)
        self.bottom_table.setSpan(0, 2, 2, 1)  # WEIGHT (span 2 rows)
        self.bottom_table.setSpan(0, 3, 1, total_cols - 3)  # SIZE header span

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
            item.setFont(QFont("Courier New", self.table_font_size, QFont.Weight.Bold))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.bottom_table.setItem(row, col, item)

        # Set size headers in row 1 (below merged SIZE header)
        for col in range(3, total_cols):
            item = QTableWidgetItem()
            # Copy size names from top table
            if (col - 3) < (self.top_table.columnCount() - 2):
                size_item = self.top_table.item(1, col - 1)  # Adjust for extra column
                if size_item:
                    item.setText(size_item.text())
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFont(QFont("Courier New", self.table_font_size))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.bottom_table.setItem(1, col, item)

        # Configure table appearance
        self.bottom_table.horizontalHeader().setVisible(False)
        self.bottom_table.verticalHeader().setVisible(False)
        self.bottom_table.setShowGrid(True)
        self.bottom_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Set column widths
        self.bottom_table.setColumnWidth(0, self.panel_name_col_width)
        self.bottom_table.setColumnWidth(1, self.panel_qty_col_width)

        # Set initial width for weight column based on text length
        font_metrics = self.bottom_table.fontMetrics()
        weight_col_width = max(
            font_metrics.horizontalAdvance("DOWN WEIGHT"),
            font_metrics.horizontalAdvance("GARMENTS WEIGHT")
        ) + 20  # Add padding
        self.bottom_table.setColumnWidth(2, weight_col_width)

        for col in range(3, total_cols):
            self.bottom_table.setColumnWidth(col, self.sewing_area_col_width)

        # Initialize data rows (starting from row 2)
        self.update_bottom_table()


    def update_bottom_table(self):
        if not hasattr(self, 'bottom_table') or not self.bottom_table:
            return

        # Prevent recursion during updates
        if getattr(self, '_updating_bottom_table', False):
            return

        self._updating_bottom_table = True

        try:
            # Get input weights
            try:
                ecodown_weight = float(self.ecodown_input.text()) if self.ecodown_input.text() else 0.0
            except:
                ecodown_weight = 0.0
            try:
                garment_weight = float(self.garment_weight_input.text()) if self.garment_weight_input.text() else 0.0
            except:
                garment_weight = 0.0

            # Get base size column from top table
            base_size = self.base_size_combo.currentText()
            base_col_top = None
            if base_size:
                for col in range(2, self.top_table.columnCount()):
                    item = self.top_table.item(1, col)
                    if item and item.text().strip() == base_size:
                        base_col_top = col
                        break

            # Calculate total sewing area for base size
            total_base_area = 0.0
            if base_col_top is not None:
                for row in range(2, self.top_table.rowCount() - 1):
                    qty_item = self.top_table.item(row, 1)
                    area_item = self.top_table.item(row, base_col_top)
                    try:
                        qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 1
                        area = float(area_item.text()) if area_item and area_item.text() else 0.0
                        total_base_area += qty * area
                    except:
                        continue

            # Clear previous highlights in bottom_table only
            for row in range(self.bottom_table.rowCount()):
                for col in range(3, self.bottom_table.columnCount()):  # Skip first 3 cols
                    item = self.bottom_table.item(row, col)
                    if item:
                        font = item.font()
                        font.setBold(False)
                        item.setFont(font)
                        item.setForeground(QColor(0, 0, 0))  # Reset to black

            # Update each panel's data (starting from row 2 in bottom table)
            for top_row in range(2, self.top_table.rowCount() - 1):
                bottom_row = 2 + ((top_row - 2) * 2)

                # Panel name and quantity (merged across 2 rows)
                name_item = self.top_table.item(top_row, 0)
                qty_item = self.top_table.item(top_row, 1)

                # Check if panel quantity is valid
                try:
                    panel_qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 0
                except:
                    panel_qty = 0

                is_valid_panel = panel_qty > 0
                show_garment_label = is_valid_panel and garment_weight > 0

                # Set panel name
                name_cell = self.bottom_table.item(bottom_row, 0)
                if not name_cell:
                    name_cell = QTableWidgetItem()
                    name_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.bottom_table.setItem(bottom_row, 0, name_cell)
                name_cell.setText(name_item.text() if name_item and is_valid_panel else "")
                self.bottom_table.setSpan(bottom_row, 0, 2, 1)
                self.bottom_table.setRowHidden(bottom_row, not is_valid_panel)
                self.bottom_table.setRowHidden(bottom_row + 1, not show_garment_label)

                # Set panel quantity with "1X" prefix
                qty_cell = self.bottom_table.item(bottom_row, 1)
                if not qty_cell:
                    qty_cell = QTableWidgetItem()
                    qty_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    qty_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.bottom_table.setItem(bottom_row, 1, qty_cell)
                try:
                    qty_value = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 0
                except:
                    qty_value = 0
                qty_cell.setText(f"1X{qty_value}" if qty_value > 0 else "")
                self.bottom_table.setSpan(bottom_row, 1, 2, 1)

                # Set weight labels explicitly
                down_label_cell = self.bottom_table.item(bottom_row, 2)
                if not down_label_cell:
                    down_label_cell = QTableWidgetItem("DOWN WEIGHT")
                    down_label_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    down_label_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.bottom_table.setItem(bottom_row, 2, down_label_cell)
                else:
                    down_label_cell.setText("DOWN WEIGHT" if is_valid_panel else "")

                garment_label_cell = self.bottom_table.item(bottom_row + 1, 2)
                if not garment_label_cell:
                    garment_label_cell = QTableWidgetItem("GARMENTS WEIGHT")
                    garment_label_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    garment_label_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.bottom_table.setItem(bottom_row + 1, 2, garment_label_cell)
                else:
                    garment_label_cell.setText("GARMENTS WEIGHT" if show_garment_label else "")

                # Skip further processing if panel is invalid
                if not is_valid_panel:
                    for col in range(3, self.bottom_table.columnCount()):
                        down_cell = self.bottom_table.item(bottom_row, col)
                        if not down_cell:
                            down_cell = QTableWidgetItem()
                            down_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            down_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                            self.bottom_table.setItem(bottom_row, col, down_cell)
                        down_cell.setText("")
                        garment_cell = self.bottom_table.item(bottom_row + 1, col)
                        if garment_cell:
                            garment_cell.setText("")
                    continue

                # Calculate and set weights for each size
                if base_col_top is not None and total_base_area > 0:
                    base_area_item = self.top_table.item(top_row, base_col_top)
                    try:
                        base_area = float(base_area_item.text()) if base_area_item and base_area_item.text() else 0.0
                        base_sewing_area = panel_qty * base_area
                    except:
                        base_sewing_area = 0.0

                    for col in range(3, self.bottom_table.columnCount()):
                        top_col = col - 1
                        if top_col >= self.top_table.columnCount():
                            continue

                        area_item = self.top_table.item(top_row, top_col)
                        try:
                            size_area = float(area_item.text()) if area_item and area_item.text() else 0.0
                            sewing_area = panel_qty * size_area
                        except:
                            sewing_area = 0.0

                        if base_sewing_area > 0:
                            # Distribute based on panel quantity
                            down_weight_val = (ecodown_weight / total_base_area) * sewing_area
                            garment_weight_val = (garment_weight / total_base_area) * sewing_area

                            # Distribute per panel
                            if panel_qty > 0:
                                down_weight_val /= panel_qty
                                garment_weight_val /= panel_qty
                        else:
                            down_weight_val = 0.0
                            garment_weight_val = 0.0

                        # Down weight row
                        down_cell = self.bottom_table.item(bottom_row, col)
                        if not down_cell:
                            down_cell = QTableWidgetItem()
                            down_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            down_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                            self.bottom_table.setItem(bottom_row, col, down_cell)
                        down_cell.setText(f"{down_weight_val:.2f}" if down_weight_val != 0 else "")

                        # Garment weight row
                        garment_cell = self.bottom_table.item(bottom_row + 1, col)
                        if garment_weight > 0:
                            if not garment_cell:
                                garment_cell = QTableWidgetItem()
                                garment_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                garment_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                                self.bottom_table.setItem(bottom_row + 1, col, garment_cell)
                            garment_cell.setText(f"{garment_weight_val:.2f}" if garment_weight_val != 0 else "")
                        else:
                            if garment_cell:
                                garment_cell.setText("")

                        # Apply bold and blue highlight to this column in bottom_table only
                        if base_col_top is not None and top_col == base_col_top:
                            font = down_cell.font()
                            font.setBold(True)
                            down_cell.setFont(font)
                            down_cell.setForeground(QColor(0, 0, 255))  # Blue
                            if garment_cell:
                                g_font = garment_cell.font()
                                g_font.setBold(True)
                                garment_cell.setFont(g_font)
                                garment_cell.setForeground(QColor(0, 0, 255))
                else:
                    # No valid base size - clear all values
                    for col in range(3, self.bottom_table.columnCount()):
                        down_cell = self.bottom_table.item(bottom_row, col)
                        if not down_cell:
                            down_cell = QTableWidgetItem()
                            down_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            down_cell.setFlags(Qt.ItemFlag.NoItemFlags)
                            self.bottom_table.setItem(bottom_row, col, down_cell)
                        down_cell.setText("")
                        garment_cell = self.bottom_table.item(bottom_row + 1, col)
                        if garment_cell:
                            garment_cell.setText("")

            # Auto-resize weight column to fit content
            self.bottom_table.resizeColumnToContents(2)
            font_metrics = self.bottom_table.fontMetrics()
            min_width = max(
                font_metrics.horizontalAdvance("DOWN WEIGHT"),
                font_metrics.horizontalAdvance("GARMENTS WEIGHT")
            ) + 20
            if self.bottom_table.columnWidth(2) < min_width:
                self.bottom_table.setColumnWidth(2, min_width)

            # Ensure all cells are centered
            for row in range(self.bottom_table.rowCount()):
                for col in range(self.bottom_table.columnCount()):
                    item = self.bottom_table.item(row, col)
                    if item:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Update totals
            self.update_bottom_totals()

        finally:
            self._updating_bottom_table = False  # Always reset the flag
        

    def update_bottom_totals(self):
        if not hasattr(self, 'bottom_table') or not self.bottom_table:
            return

        total_rows = self.bottom_table.rowCount()
        total_cols = self.bottom_table.columnCount()

        down_totals = [0.0] * (total_cols - 3)
        garment_totals = [0.0] * (total_cols - 3)

        for row in range(2, total_rows - 2, 2):  # Skip header and total rows
            qty_item = self.bottom_table.item(row, 1)
            try:
                qty = int(qty_item.text().replace("1X", "")) if qty_item and qty_item.text().startswith("1X") else 1
            except:
                qty = 1

            for i, col in enumerate(range(3, total_cols)):
                down_cell = self.bottom_table.item(row, col)
                try:
                    down_val = float(down_cell.text()) if down_cell and down_cell.text() else 0.0
                    down_totals[i] += down_val * qty
                except:
                    pass

                garment_row = row + 1
                if not self.bottom_table.isRowHidden(garment_row):
                    garment_cell = self.bottom_table.item(garment_row, col)
                    try:
                        g_val = float(garment_cell.text()) if garment_cell and garment_cell.text() else 0.0
                        garment_totals[i] += g_val * qty
                    except:
                        pass

        # TOTAL DOWN WEIGHT row
        total_row = total_rows - 2
        self.bottom_table.setSpan(total_row, 0, 1, 3)
        self.bottom_table.setRowHidden(total_row, False)
        label_item = QTableWidgetItem("TOTAL DOWN WEIGHT")
        label_item.setFlags(Qt.ItemFlag.NoItemFlags)
        label_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        label_item.setFont(QFont("Courier New", self.table_font_size, QFont.Weight.Bold))
        self.bottom_table.setItem(total_row, 0, label_item)

        for i, col in enumerate(range(3, total_cols)):
            item = QTableWidgetItem(f"{round(down_totals[i]):.0f}")  # Rounded
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.bottom_table.setItem(total_row, col, item)

        # GARMENT TOTAL row
        total_row = total_rows - 1
        self.bottom_table.setSpan(total_row, 0, 1, 3)
        show_garments_total = float(self.garment_weight_input.text() or 0) > 0
        self.bottom_table.setRowHidden(total_row, not show_garments_total)

        if show_garments_total:
            label_item = QTableWidgetItem("TOTAL GARMENT WEIGHT")
            label_item.setFlags(Qt.ItemFlag.NoItemFlags)
            label_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            label_item.setFont(QFont("Courier New", self.table_font_size, QFont.Weight.Bold))
            self.bottom_table.setItem(total_row, 0, label_item)

            for i, col in enumerate(range(3, total_cols)):
                item = QTableWidgetItem(f"{round(garment_totals[i]):.0f}")  # Rounded
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bottom_table.setItem(total_row, col, item)


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
        if dialog.exec() == QDialog.DialogCode.Accepted:
            factory_name, factory_location = dialog.get_factory_info()
            self.settings.setValue("factory_name", factory_name)
            self.settings.setValue("factory_location", factory_location)
            self.update_factory_display(factory_name, factory_location)

    def update_factory_display(self, name, location):
        self.factory_name_label.setText(name)
        self.factory_location_label.setText(location)
        self.setWindowTitle(f"Automatic Down Allocation System - {name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Courier New", 10)
    app.setFont(font)

    splash_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'splash_image.png')
    pixmap = QPixmap(os.path.abspath(splash_path))

    splash = SplashScreen(pixmap, version="1.0.0")
    splash.show_centered()
    splash.start_animation(2500)

    # Declare global window reference to keep it alive
    global main_window
    main_window = None

    def transition_to_main():
        def show_main():
            splash.deleteLater()
            global main_window
            main_window = DownAllocationApp()
            main_window.showMaximized()

        splash.fade_out(callback=show_main)

    QTimer.singleShot(2700, transition_to_main)

    sys.exit(app.exec())